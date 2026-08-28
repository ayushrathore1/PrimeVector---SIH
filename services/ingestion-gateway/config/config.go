package config

import (
	"os"
	"strconv"
	"time"
)

// Config holds configuration parameters for IngestionGateway.
type Config struct {
	// ServerPort is the TCP port on which gRPC server listens (default: 50051)
	ServerPort int

	// Region is the geographic identifier of this gateway deployment (e.g. "in-mumbai-1", "ap-south-1")
	Region string

	// StreamBufferDepth is the bounded channel capacity per active stream for backpressure flow control
	StreamBufferDepth int

	// MaxConcurrentStreams is the total maximum concurrent active audio streams permitted per instance
	MaxConcurrentStreams int

	// RateLimitRPS is the default token bucket refill rate (chunks/sec) per tenant
	RateLimitRPS float64

	// RateLimitBurst is the maximum burst token capacity per tenant
	RateLimitBurst int

	// DownstreamTimeout is the maximum processing deadline for downstream inference calls
	DownstreamTimeout time.Duration

	// DownstreamURL is the base HTTP/gRPC endpoint for feature extraction / fusion pipeline
	DownstreamURL string

	// EnableCircuitBreaker enables automatic fail-safe trip when downstream errors exceed threshold
	EnableCircuitBreaker bool
}

// LoadFromEnv loads configuration parameters with sensible production defaults.
func LoadFromEnv() *Config {
	cfg := &Config{
		ServerPort:           getEnvAsInt("PORT", 50051),
		Region:               getEnv("REGION", "in-mumbai-1"),
		StreamBufferDepth:    getEnvAsInt("STREAM_BUFFER_DEPTH", 8),
		MaxConcurrentStreams: getEnvAsInt("MAX_CONCURRENT_STREAMS", 50000),
		RateLimitRPS:         getEnvAsFloat("RATE_LIMIT_RPS", 100.0),
		RateLimitBurst:       getEnvAsInt("RATE_LIMIT_BURST", 200),
		DownstreamTimeout:    getEnvAsDuration("DOWNSTREAM_TIMEOUT", 250*time.Millisecond),
		DownstreamURL:        getEnv("DOWNSTREAM_URL", "http://feature-extraction-service:8000"),
		EnableCircuitBreaker: getEnvAsBool("ENABLE_CIRCUIT_BREAKER", true),
	}
	return cfg
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}

func getEnvAsInt(key string, defaultVal int) int {
	if val := os.Getenv(key); val != "" {
		if i, err := strconv.Atoi(val); err == nil {
			return i
		}
	}
	return defaultVal
}

func getEnvAsFloat(key string, defaultVal float64) float64 {
	if val := os.Getenv(key); val != "" {
		if f, err := strconv.ParseFloat(val, 64); err == nil {
			return f
		}
	}
	return defaultVal
}

func getEnvAsBool(key string, defaultVal bool) bool {
	if val := os.Getenv(key); val != "" {
		if b, err := strconv.ParseBool(val); err == nil {
			return b
		}
	}
	return defaultVal
}

func getEnvAsDuration(key string, defaultVal time.Duration) time.Duration {
	if val := os.Getenv(key); val != "" {
		if d, err := time.ParseDuration(val); err == nil {
			return d
		}
	}
	return defaultVal
}
