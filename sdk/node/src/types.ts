/**
 * Voice Integrity Node.js SDK (voiceintegrity.v1)
 *
 * Types mapping 1:1 to proto/risk_assessment.proto data structures.
 */

/**
 * Enrollment status of the speaker.
 * Mirrors voiceintegrity.v1.EnrollmentStatus enum.
 */
export const EnrollmentStatus = {
  ENROLLMENT_STATUS_UNSPECIFIED: "ENROLLMENT_STATUS_UNSPECIFIED",
  NOT_ENROLLED: "NOT_ENROLLED",
  ENROLLED: "ENROLLED",
  ENROLLMENT_REVOKED: "ENROLLMENT_REVOKED",
} as const;

export type EnrollmentStatus =
  (typeof EnrollmentStatus)[keyof typeof EnrollmentStatus];

/**
 * Recommended action returned by the risk fusion engine.
 * Mirrors voiceintegrity.v1.RecommendedAction enum.
 */
export const RecommendedAction = {
  ACTION_UNSPECIFIED: "ACTION_UNSPECIFIED",
  PROCEED: "PROCEED",
  RECOMMEND_CALLBACK_VERIFICATION: "RECOMMEND_CALLBACK_VERIFICATION",
  RECOMMEND_MFA_STEP_UP: "RECOMMEND_MFA_STEP_UP",
  RECOMMEND_SUPERVISOR_ESCALATION: "RECOMMEND_SUPERVISOR_ESCALATION",
  BLOCK_PENDING_VERIFICATION: "BLOCK_PENDING_VERIFICATION",
} as const;

export type RecommendedAction =
  (typeof RecommendedAction)[keyof typeof RecommendedAction];

/**
 * One independent evidence signal feeding the fusion engine.
 * Mirrors voiceintegrity.v1.RiskSignal message.
 */
export interface RiskSignal {
  /** 0.0-1.0, higher = more suspicious */
  score: number;
  /** 0.0-1.0, model's confidence in `score` itself */
  confidence: number;
  /** false if this signal could not be computed */
  available?: boolean;
  /** short human-readable reason, for audit/UI */
  detail?: string;
}

/**
 * Request message for RiskFusionEngine.Assess.
 * Mirrors voiceintegrity.v1.RiskAssessmentRequest message.
 */
export interface RiskAssessmentRequest {
  /** Unique call session identifier */
  call_session_id: string;
  /** Tenant / organization identifier */
  tenant_id: string;
  /** Synthesis/spoof detection signal */
  synthesis_signal: RiskSignal;
  /** Speaker verification signal */
  speaker_match_signal: RiskSignal;
  /** Contextual metadata risk signal */
  contextual_signal: RiskSignal;
  /** Enrollment status of subject */
  enrollment_status?: EnrollmentStatus;
}

/**
 * Response message from RiskFusionEngine.Assess.
 * Mirrors voiceintegrity.v1.RiskAssessmentResponse message.
 */
export interface RiskAssessmentResponse {
  /** Unique call session identifier echoed back */
  call_session_id: string;
  /** Fused composite score between 0.0 and 1.0 */
  risk_score: number;
  /** Fused confidence rating between 0.0 and 1.0 */
  confidence: number;
  /** Ordered list of recommended actions */
  actions: RecommendedAction[];
  /** Human-readable explanation built from contributing signals */
  explanation: string;
  /** ISO-8601 evaluation timestamp */
  evaluated_at: string;
  /** True if computed under partial-signal/fail-safe mode */
  degraded: boolean;
}

/**
 * Configuration options for initializing VoiceIntegrityClient.
 */
export interface ClientOptions {
  /** Base URL of the Voice Integrity service (e.g. 'https://api.voiceintegrity.example.com') */
  baseUrl: string;
  /** API key for authentication via X-API-Key header */
  apiKey?: string;
  /** Request timeout in milliseconds (default: 5000) */
  timeoutMs?: number;
}
