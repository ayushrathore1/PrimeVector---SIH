/**
 * Thin client implementation for RiskFusionEngine (voiceintegrity.v1).
 *
 * No hidden retries — all network and API errors bubble up directly to the caller.
 */

import { APIError, ConnectionError } from "./errors.ts";
import {
  EnrollmentStatus,
  RecommendedAction,
} from "./types.ts";
import type {
  ClientOptions,
  RiskAssessmentRequest,
  RiskAssessmentResponse,
} from "./types.ts";

export class VoiceIntegrityClient {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly timeoutMs: number;

  constructor(options: ClientOptions) {
    if (!options.baseUrl) {
      throw new Error("baseUrl is required");
    }
    this.baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.apiKey = options.apiKey;
    this.timeoutMs = options.timeoutMs ?? 5000;
  }

  /**
   * Evaluate real-time risk assessment signals for a call session.
   *
   * Maps 1:1 to proto RPC:
   * `rpc Assess(RiskAssessmentRequest) returns (RiskAssessmentResponse)`
   *
   * @param request The risk assessment input payload containing acoustic & contextual signals.
   *
   * Request Shape:
   * ```json
   * {
   *   "call_session_id": "string",
   *   "tenant_id": "string",
   *   "synthesis_signal": {
   *     "score": 0.0,       // 0.0-1.0 (synthesis/acoustic spoof detection)
   *     "confidence": 0.0,  // 0.0-1.0
   *     "available": true,  // boolean
   *     "detail": "string"  // string
   *   },
   *   "speaker_match_signal": {
   *     "score": 0.0,       // 0.0-1.0 (speaker mismatch score)
   *     "confidence": 0.0,  // 0.0-1.0
   *     "available": true,  // false if unenrolled
   *     "detail": "string"  // string
   *   },
   *   "contextual_signal": {
   *     "score": 0.0,       // 0.0-1.0 (transaction/metadata risk factor)
   *     "confidence": 0.0,  // 0.0-1.0
   *     "available": true,  // boolean
   *     "detail": "string"  // string
   *   },
   *   "enrollment_status": "ENROLLMENT_STATUS_UNSPECIFIED" | "NOT_ENROLLED" | "ENROLLED" | "ENROLLMENT_REVOKED"
   * }
   * ```
   *
   * Response Shape:
   * ```json
   * {
   *   "call_session_id": "string",
   *   "risk_score": 0.0,       // fused composite score (0.0 - 1.0)
   *   "confidence": 0.0,       // fused confidence rating (0.0 - 1.0)
   *   "actions": [             // ordered array of recommended actions
   *     "PROCEED" |
   *     "RECOMMEND_CALLBACK_VERIFICATION" |
   *     "RECOMMEND_MFA_STEP_UP" |
   *     "RECOMMEND_SUPERVISOR_ESCALATION" |
   *     "BLOCK_PENDING_VERIFICATION"
   *   ],
   *   "explanation": "string", // human-readable explanation
   *   "evaluated_at": "string",// ISO-8601 timestamp
   *   "degraded": false        // boolean (fail-safe indicator)
   * }
   * ```
   *
   * @throws {APIError} If the server returns a 4xx or 5xx HTTP status code.
   * @throws {ConnectionError} If a network error or timeout occurs.
   */
  public async assess(
    request: RiskAssessmentRequest
  ): Promise<RiskAssessmentResponse> {
    const url = `${this.baseUrl}/v1/assess`;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };

    if (this.apiKey) {
      headers["X-API-Key"] = this.apiKey;
    }

    const payload = {
      call_session_id: request.call_session_id,
      tenant_id: request.tenant_id,
      synthesis_signal: {
        score: request.synthesis_signal.score,
        confidence: request.synthesis_signal.confidence,
        available: request.synthesis_signal.available ?? true,
        detail: request.synthesis_signal.detail ?? "",
      },
      speaker_match_signal: {
        score: request.speaker_match_signal.score,
        confidence: request.speaker_match_signal.confidence,
        available: request.speaker_match_signal.available ?? true,
        detail: request.speaker_match_signal.detail ?? "",
      },
      contextual_signal: {
        score: request.contextual_signal.score,
        confidence: request.contextual_signal.confidence,
        available: request.contextual_signal.available ?? true,
        detail: request.contextual_signal.detail ?? "",
      },
      enrollment_status:
        request.enrollment_status ??
        EnrollmentStatus.ENROLLMENT_STATUS_UNSPECIFIED,
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    let response: Response;
    try {
      response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === "AbortError") {
        throw new ConnectionError(`Request timed out after ${this.timeoutMs}ms`, err);
      }
      throw new ConnectionError(`Network request failed: ${err.message}`, err);
    } finally {
      clearTimeout(timeoutId);
    }

    const text = await response.text();

    if (!response.ok) {
      throw new APIError(response.status, text, text);
    }

    let parsed: any;
    try {
      parsed = JSON.parse(text);
    } catch (err: any) {
      throw new APIError(
        response.status,
        "Failed to parse JSON response from server",
        text
      );
    }

    const actions: RecommendedAction[] = (parsed.actions || []).map((a: string) => {
      if (Object.values(RecommendedAction).includes(a as RecommendedAction)) {
        return a as RecommendedAction;
      }
      return RecommendedAction.ACTION_UNSPECIFIED;
    });

    return {
      call_session_id: String(parsed.call_session_id || ""),
      risk_score: Number(parsed.risk_score || 0),
      confidence: Number(parsed.confidence || 0),
      actions,
      explanation: String(parsed.explanation || ""),
      evaluated_at: String(parsed.evaluated_at || ""),
      degraded: Boolean(parsed.degraded),
    };
  }
}
