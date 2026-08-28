package main

import (
	"fmt"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"syscall"

	"voiceintegrity/ingestion-gateway/config"
	"voiceintegrity/ingestion-gateway/internal/downstream"
	"voiceintegrity/ingestion-gateway/internal/limiter"
	"voiceintegrity/ingestion-gateway/internal/server"
	"voiceintegrity/ingestion-gateway/internal/telemetry"
	pb "voiceintegrity/ingestion-gateway/pkg/pb"

	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
)

func main() {
	cfg := config.LoadFromEnv()
	logger := telemetry.InitLogger(cfg.Region)

	logger.Info("starting ingestion-gateway",
		slog.Int("port", cfg.ServerPort),
		slog.String("region", cfg.Region),
		slog.Int("stream_buffer_depth", cfg.StreamBufferDepth),
		slog.Float64("rate_limit_rps", cfg.RateLimitRPS),
		slog.Duration("downstream_timeout", cfg.DownstreamTimeout),
		slog.String("downstream_url", cfg.DownstreamURL),
	)

	// Initialize components
	tenantLimiter := limiter.NewTenantLimiter(cfg.RateLimitRPS, cfg.RateLimitBurst)
	downstreamProcessor := downstream.NewHTTPDownstreamClient(cfg.DownstreamURL, cfg.DownstreamTimeout)
	gwServer := server.NewGatewayServer(cfg, tenantLimiter, downstreamProcessor, logger)

	lis, err := net.Listen("tcp", fmt.Sprintf(":%d", cfg.ServerPort))
	if err != nil {
		logger.Error("failed to listen on tcp port", slog.Any("error", err))
		os.Exit(1)
	}

	grpcServer := grpc.NewServer(
		grpc.MaxConcurrentStreams(uint32(cfg.MaxConcurrentStreams)),
	)

	pb.RegisterIngestionGatewayServer(grpcServer, gwServer)
	reflection.Register(grpcServer)

	// Graceful shutdown channel
	stopChan := make(chan os.Signal, 1)
	signal.Notify(stopChan, os.Interrupt, syscall.SIGTERM)

	go func() {
		logger.Info("gRPC ingestion gateway listening", slog.String("addr", lis.Addr().String()))
		if err := grpcServer.Serve(lis); err != nil && err != grpc.ErrServerStopped {
			logger.Error("gRPC server error", slog.Any("error", err))
		}
	}()

	<-stopChan
	logger.Info("shutting down ingestion-gateway gracefully...")
	grpcServer.GracefulStop()
	logger.Info("ingestion-gateway stopped")
}
