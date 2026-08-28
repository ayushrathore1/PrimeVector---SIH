package server

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"sync/atomic"

	"voiceintegrity/ingestion-gateway/config"
	"voiceintegrity/ingestion-gateway/internal/downstream"
	"voiceintegrity/ingestion-gateway/internal/limiter"
	"voiceintegrity/ingestion-gateway/internal/telemetry"
	pb "voiceintegrity/ingestion-gateway/pkg/pb"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/timestamppb"
)

// GatewayServer implements the gRPC IngestionGateway service.
type GatewayServer struct {
	pb.UnimplementedIngestionGatewayServer
	cfg        *config.Config
	limiter    *limiter.TenantLimiter
	downstream downstream.DownstreamProcessor
	logger     *slog.Logger
}

// NewGatewayServer creates a new GatewayServer instance.
func NewGatewayServer(
	cfg *config.Config,
	limiter *limiter.TenantLimiter,
	downstream downstream.DownstreamProcessor,
	logger *slog.Logger,
) *GatewayServer {
	return &GatewayServer{
		cfg:        cfg,
		limiter:    limiter,
		downstream: downstream,
		logger:     logger,
	}
}

// Ping implements the health and region ping RPC.
func (s *GatewayServer) Ping(ctx context.Context, req *pb.PingRequest) (*pb.PingResponse, error) {
	region := s.extractRegion(ctx)
	return &pb.PingResponse{
		Message:   "pong: " + req.GetMessage(),
		Region:    region,
		Timestamp: timestamppb.Now(),
	}, nil
}

// StreamAudio handles bidirectional gRPC streaming of audio chunks to continuous risk assessments.
func (s *GatewayServer) StreamAudio(stream pb.IngestionGateway_StreamAudioServer) error {
	ctx := stream.Context()
	region := s.extractRegion(ctx)

	// Check global active streams capacity
	if s.cfg.MaxConcurrentStreams > 0 {
		active := atomic.LoadInt64(&telemetry.GlobalMetrics.ActiveStreams)
		if active >= int64(s.cfg.MaxConcurrentStreams) {
			s.logger.WarnContext(ctx, "gateway saturated: max concurrent streams exceeded",
				slog.Int64("active_streams", active),
				slog.Int("max_allowed", s.cfg.MaxConcurrentStreams),
			)
			return status.Errorf(codes.ResourceExhausted, "gateway capacity reached (%d streams active)", active)
		}
	}

	telemetry.GlobalMetrics.IncActiveStreams()
	defer telemetry.GlobalMetrics.DecActiveStreams()

	// Stream-level context and metadata
	var (
		sessionID string
		tenantID  string
		chunkCount int64
	)

	// Bounded channel per active stream for backpressure flow control
	bufferDepth := s.cfg.StreamBufferDepth
	if bufferDepth <= 0 {
		bufferDepth = 8
	}
	chunkQueue := make(chan *pb.AudioChunkRequest, bufferDepth)
	errChan := make(chan error, 2)

	// Ingress goroutine: reads audio chunks from client stream
	go func() {
		defer close(chunkQueue)
		for {
			chunk, err := stream.Recv()
			if err != nil {
				if errors.Is(err, io.EOF) {
					// Clean client close
					return
				}
				select {
				case errChan <- err:
				default:
				}
				return
			}

			if chunk == nil {
				continue
			}

			telemetry.GlobalMetrics.IncChunksIngested()

			// Initialize session & tenant context from first chunk
			if sessionID == "" {
				sessionID = chunk.GetCallSessionId()
				tenantID = chunk.GetTenantId()
				s.logger.InfoContext(ctx, "started audio ingestion stream",
					slog.String("session_id", sessionID),
					slog.String("tenant_id", tenantID),
					slog.String("region", region),
				)
			}

			// Tenant rate limiting check
			if currentTenant := chunk.GetTenantId(); currentTenant != "" {
				if err := s.limiter.Allow(currentTenant); err != nil {
					telemetry.GlobalMetrics.IncRateLimitRejections()
					s.logger.WarnContext(ctx, "tenant rate limit exceeded",
						slog.String("tenant_id", currentTenant),
						slog.String("session_id", sessionID),
					)
					select {
					case errChan <- err:
					default:
					}
					return
				}
			}

			// Bounded channel send applies backpressure directly to stream.Recv()
			// If downstream queue is saturated, select will wait or track backpressure event
			select {
			case chunkQueue <- chunk:
			case <-ctx.Done():
				return
			default:
				// Channel is full: record backpressure event and block until slot is available
				telemetry.GlobalMetrics.IncBackpressureEvents()
				select {
				case chunkQueue <- chunk:
				case <-ctx.Done():
					return
				}
			}

			if chunk.GetIsLastChunk() {
				return
			}
		}
	}()

	// Egress / Downstream processing loop
	for {
		select {
		case err := <-errChan:
			s.logger.InfoContext(ctx, "stream terminated with status",
				slog.String("session_id", sessionID),
				slog.String("tenant_id", tenantID),
				slog.Any("error", err),
			)
			return err

		case <-ctx.Done():
			return ctx.Err()

		case chunk, ok := <-chunkQueue:
			if !ok {
				// Chunk queue exhausted and closed
				s.logger.InfoContext(ctx, "audio ingestion stream completed successfully",
					slog.String("session_id", sessionID),
					slog.String("tenant_id", tenantID),
					slog.Int64("total_chunks", chunkCount),
					slog.String("region", region),
				)
				return nil
			}

			chunkCount++

			// Process audio chunk downstream with timeout
			downstreamCtx, cancel := context.WithTimeout(ctx, s.cfg.DownstreamTimeout)
			resp, err := s.downstream.ProcessAudioChunk(downstreamCtx, chunk)
			cancel()

			if err != nil {
				// Fail-safe behavior (DESIGN.md §3 & §4.7):
				// Downstream outage / timeout / error degrades gracefully to manual verification recommendation
				telemetry.GlobalMetrics.IncDownstreamErrors()
				telemetry.GlobalMetrics.IncFailsafeEvaluations()

				s.logger.WarnContext(ctx, "downstream processing degraded, emitting fail-safe response",
					slog.String("session_id", chunk.GetCallSessionId()),
					slog.Int64("sequence_number", chunk.GetSequenceNumber()),
					slog.Any("downstream_error", err),
				)

				resp = downstream.BuildFailsafeResponse(chunk.GetCallSessionId(), err.Error())
			}

			telemetry.GlobalMetrics.IncChunksProcessed()

			// Send RiskAssessmentResponse update back to client
			if err := stream.Send(resp); err != nil {
				s.logger.ErrorContext(ctx, "failed to stream risk assessment to client",
					slog.String("session_id", chunk.GetCallSessionId()),
					slog.Any("error", err),
				)
				return err
			}
		}
	}
}

// extractRegion extracts the regional routing tag from gRPC incoming metadata.
func (s *GatewayServer) extractRegion(ctx context.Context) string {
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if vals := md.Get("x-region"); len(vals) > 0 && vals[0] != "" {
			return vals[0]
		}
		if vals := md.Get("region"); len(vals) > 0 && vals[0] != "" {
			return vals[0]
		}
	}
	return s.cfg.Region
}
