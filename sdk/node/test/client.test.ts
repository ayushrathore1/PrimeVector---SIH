import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";

// Minimal inline build or test against source/transpiled
// Testing JavaScript equivalents directly to test client mechanics
import { VoiceIntegrityClient } from "../src/client.ts";
import { EnrollmentStatus, RecommendedAction } from "../src/types.ts";
import { APIError, ConnectionError } from "../src/errors.ts";

test("VoiceIntegrityClient - assess success", async (t) => {
  let receivedApiKey = "";
  let receivedBody = "";

  const server = http.createServer((req, res) => {
    receivedApiKey = req.headers["x-api-key"] || "";
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
    });
    req.on("end", () => {
      receivedBody = body;
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          call_session_id: "sess-node-001",
          risk_score: 0.92,
          confidence: 0.95,
          actions: ["RECOMMEND_CALLBACK_VERIFICATION", "RECOMMEND_SUPERVISOR_ESCALATION"],
          explanation: "synthesis artifacts detected",
          evaluated_at: "2026-08-28T18:00:00Z",
          degraded: false,
        })
      );
    });
  });

  await new Promise((resolve) => server.listen(0, resolve));
  const port = (server.address() as any).port;

  const client = new VoiceIntegrityClient({
    baseUrl: `http://127.0.0.1:${port}`,
    apiKey: "test_node_key_999",
    timeoutMs: 3000,
  });

  const response = await client.assess({
    call_session_id: "sess-node-001",
    tenant_id: "tenant-bank",
    synthesis_signal: { score: 0.9, confidence: 0.95, available: true, detail: "synth" },
    speaker_match_signal: { score: 0.8, confidence: 0.9, available: true, detail: "mismatch" },
    contextual_signal: { score: 0.5, confidence: 1.0, available: true, detail: "context" },
    enrollment_status: EnrollmentStatus.ENROLLED,
  });

  assert.equal(receivedApiKey, "test_node_key_999");
  const parsedBody = JSON.parse(receivedBody);
  assert.equal(parsedBody.call_session_id, "sess-node-001");
  assert.equal(parsedBody.enrollment_status, "ENROLLED");

  assert.equal(response.call_session_id, "sess-node-001");
  assert.equal(response.risk_score, 0.92);
  assert.equal(response.confidence, 0.95);
  assert.deepEqual(response.actions, [
    RecommendedAction.RECOMMEND_CALLBACK_VERIFICATION,
    RecommendedAction.RECOMMEND_SUPERVISOR_ESCALATION,
  ]);
  assert.equal(response.degraded, false);

  server.close();
});

test("VoiceIntegrityClient - API error", async (t) => {
  const server = http.createServer((req, res) => {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end("Invalid signal payload");
  });

  await new Promise((resolve) => server.listen(0, resolve));
  const port = (server.address() as any).port;

  const client = new VoiceIntegrityClient({
    baseUrl: `http://127.0.0.1:${port}`,
    timeoutMs: 3000,
  });

  await assert.rejects(
    async () => {
      await client.assess({
        call_session_id: "sess-node-err",
        tenant_id: "tenant-bank",
        synthesis_signal: { score: 1.5, confidence: 0.95 },
        speaker_match_signal: { score: 0.8, confidence: 0.9 },
        contextual_signal: { score: 0.5, confidence: 1.0 },
      });
    },
    (err: any) => {
      assert.ok(err instanceof APIError);
      assert.equal(err.statusCode, 400);
      assert.match(err.message, /Invalid signal payload/);
      return true;
    }
  );

  server.close();
});

test("VoiceIntegrityClient - Connection error", async (t) => {
  const client = new VoiceIntegrityClient({
    baseUrl: "http://127.0.0.1:59999", // Unreachable port
    timeoutMs: 500,
  });

  await assert.rejects(
    async () => {
      await client.assess({
        call_session_id: "sess-node-conn",
        tenant_id: "tenant-bank",
        synthesis_signal: { score: 0.5, confidence: 0.95 },
        speaker_match_signal: { score: 0.8, confidence: 0.9 },
        contextual_signal: { score: 0.5, confidence: 1.0 },
      });
    },
    (err: any) => {
      assert.ok(err instanceof ConnectionError);
      return true;
    }
  );
});
