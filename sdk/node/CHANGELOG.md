# Changelog

All notable changes to the Voice Integrity Node.js SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-28

### Added
- Initial release of `@voiceintegrity/sdk` Node.js SDK mapping to `voiceintegrity.v1` (`proto/risk_assessment.proto`).
- Enums: `EnrollmentStatus`, `RecommendedAction`.
- Interfaces: `RiskSignal`, `RiskAssessmentRequest`, `RiskAssessmentResponse`, `ClientOptions`.
- Client: `VoiceIntegrityClient.assess` method with zero hidden retries.
- Custom errors: `VoiceIntegrityError`, `APIError`, `ConnectionError`.
