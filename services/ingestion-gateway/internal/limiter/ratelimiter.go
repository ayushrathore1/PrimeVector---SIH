package limiter

import (
	"context"
	"fmt"
	"sync"
	"time"

	"golang.org/x/time/rate"
	"google.golang.org/genproto/googleapis/rpc/errdetails"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/durationpb"
)

// TenantLimiter provides per-tenant token-bucket rate limiting with gRPC 429 status generation.
type TenantLimiter struct {
	mu           sync.RWMutex
	limiters     map[string]*tenantEntry
	defaultRPS   float64
	defaultBurst int
	cleanupTick  time.Duration
}

type tenantEntry struct {
	limiter  *rate.Limiter
	lastSeen time.Time
}

// NewTenantLimiter creates a thread-safe per-tenant rate limiter.
func NewTenantLimiter(defaultRPS float64, defaultBurst int) *TenantLimiter {
	tl := &TenantLimiter{
		limiters:     make(map[string]*tenantEntry),
		defaultRPS:   defaultRPS,
		defaultBurst: defaultBurst,
		cleanupTick:  10 * time.Minute,
	}
	go tl.cleanupLoop()
	return tl
}

func (tl *TenantLimiter) getLimiter(tenantID string) *rate.Limiter {
	tl.mu.RLock()
	entry, exists := tl.limiters[tenantID]
	tl.mu.RUnlock()

	if exists {
		entry.lastSeen = time.Now()
		return entry.limiter
	}

	tl.mu.Lock()
	defer tl.mu.Unlock()

	// Double-check after acquiring write lock
	if entry, exists = tl.limiters[tenantID]; exists {
		entry.lastSeen = time.Now()
		return entry.limiter
	}

	lim := rate.NewLimiter(rate.Limit(tl.defaultRPS), tl.defaultBurst)
	tl.limiters[tenantID] = &tenantEntry{
		limiter:  lim,
		lastSeen: time.Now(),
	}
	return lim
}

// Allow checks if a request from tenantID is allowed.
// If allowed, returns nil.
// If disallowed, returns a gRPC ResourceExhausted (429 equivalent) status error with RetryInfo.
func (tl *TenantLimiter) Allow(tenantID string) error {
	lim := tl.getLimiter(tenantID)
	if lim.Allow() {
		return nil
	}

	// Calculate estimated retry delay based on rate
	retrySeconds := 1
	if tl.defaultRPS > 0 {
		retrySeconds = int(1.0/tl.defaultRPS) + 1
	}
	retryDelay := time.Duration(retrySeconds) * time.Second

	return BuildRateLimitError(tenantID, retryDelay)
}

// Wait blocks until a token is available or context is cancelled.
func (tl *TenantLimiter) Wait(ctx context.Context, tenantID string) error {
	lim := tl.getLimiter(tenantID)
	return lim.Wait(ctx)
}

// BuildRateLimitError constructs a gRPC status error with codes.ResourceExhausted
// and attaches google.rpc.RetryInfo with retry-after hint.
func BuildRateLimitError(tenantID string, retryDelay time.Duration) error {
	st := status.New(codes.ResourceExhausted, fmt.Sprintf("tenant '%s' exceeded rate limit quota", tenantID))

	retryInfo := &errdetails.RetryInfo{
		RetryDelay: durationpb.New(retryDelay),
	}

	stWithDetails, err := st.WithDetails(retryInfo)
	if err != nil {
		// Fallback if detail marshalling fails
		return st.Err()
	}

	return stWithDetails.Err()
}

func (tl *TenantLimiter) cleanupLoop() {
	ticker := time.NewTicker(tl.cleanupTick)
	for range ticker.C {
		tl.mu.Lock()
		now := time.Now()
		for tenantID, entry := range tl.limiters {
			if now.Sub(entry.lastSeen) > 30*time.Minute {
				delete(tl.limiters, tenantID)
			}
		}
		tl.mu.Unlock()
	}
}
