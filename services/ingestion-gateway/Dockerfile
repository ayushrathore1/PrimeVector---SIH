# Build Stage
FROM golang:1.22-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git protobuf protobuf-dev

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o ingestion-gateway ./cmd/server

# Runtime Stage
FROM alpine:3.19

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

COPY --from=builder /app/ingestion-gateway .

EXPOSE 50051

ENV PORT=50051 \
    REGION=in-mumbai-1 \
    STREAM_BUFFER_DEPTH=8 \
    RATE_LIMIT_RPS=100.0 \
    RATE_LIMIT_BURST=200

ENTRYPOINT ["/app/ingestion-gateway"]
