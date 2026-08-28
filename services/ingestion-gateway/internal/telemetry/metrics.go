package telemetry

import (
	"log/slog"
	"os"
	"sync/atomic"
)

// Metrics holds atomic counters and observability indicators for ingestion-gateway.
type Metrics struct {
	ActiveStreams        int64
	TotalStreamsOpened   uint64
	TotalChunksIngested  uint64
	TotalChunksProcessed uint64
	BackpressureEvents   uint64
	RateLimitRejections  uint64
	FailsafeEvaluations  uint64
	DownstreamErrors     uint64
}

// GlobalMetrics is the singleton metrics instance.
var GlobalMetrics = &Metrics{}

func (m *Metrics) IncActiveStreams() {
	atomic.AddInt64(&m.ActiveStreams, 1)
	atomic.AddUint64(&m.TotalStreamsOpened, 1)
}

func (m *Metrics) DecActiveStreams() {
	atomic.AddInt64(&m.ActiveStreams, -1)
}

func (m *Metrics) IncChunksIngested() {
	atomic.AddUint64(&m.TotalChunksIngested, 1)
}

func (m *Metrics) IncChunksProcessed() {
	atomic.AddUint64(&m.TotalChunksProcessed, 1)
}

func (m *Metrics) IncBackpressureEvents() {
	atomic.AddUint64(&m.BackpressureEvents, 1)
}

func (m *Metrics) IncRateLimitRejections() {
	atomic.AddUint64(&m.RateLimitRejections, 1)
}

func (m *Metrics) IncFailsafeEvaluations() {
	atomic.AddUint64(&m.FailsafeEvaluations, 1)
}

func (m *Metrics) IncDownstreamErrors() {
	atomic.AddUint64(&m.DownstreamErrors, 1)
}

// Snapshot returns a copy of current metrics.
type MetricsSnapshot struct {
	ActiveStreams        int64  `json:"active_streams"`
	TotalStreamsOpened   uint64 `json:"total_streams_opened"`
	TotalChunksIngested  uint64 `json:"total_chunks_ingested"`
	TotalChunksProcessed uint64 `json:"total_chunks_processed"`
	BackpressureEvents   uint64 `json:"backpressure_events"`
	RateLimitRejections  uint64 `json:"rate_limit_rejections"`
	FailsafeEvaluations  uint64 `json:"failsafe_evaluations"`
	DownstreamErrors     uint64 `json:"downstream_errors"`
}

func (m *Metrics) Snapshot() MetricsSnapshot {
	return MetricsSnapshot{
		ActiveStreams:        atomic.LoadInt64(&m.ActiveStreams),
		TotalStreamsOpened:   atomic.LoadUint64(&m.TotalStreamsOpened),
		TotalChunksIngested:  atomic.LoadUint64(&m.TotalChunksIngested),
		TotalChunksProcessed: atomic.LoadUint64(&m.TotalChunksProcessed),
		BackpressureEvents:   atomic.LoadUint64(&m.BackpressureEvents),
		RateLimitRejections:  atomic.LoadUint64(&m.RateLimitRejections),
		FailsafeEvaluations:  atomic.LoadUint64(&m.FailsafeEvaluations),
		DownstreamErrors:     atomic.LoadUint64(&m.DownstreamErrors),
	}
}

// InitLogger initializes JSON structured logging.
func InitLogger(region string) *slog.Logger {
	handler := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	})
	logger := slog.New(handler).With(
		slog.String("service", "ingestion-gateway"),
		slog.String("region", region),
	)
	slog.SetDefault(logger)
	return logger
}
