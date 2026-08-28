# Changelog

All notable changes to the Voice Integrity Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-28

### Added
- Initial release of `voiceintegrity` Python SDK mapping to `voiceintegrity.v1` (`proto/risk_assessment.proto`).
- Enums: `EnrollmentStatus`, `RecommendedAction`.
- Dataclasses: `RiskSignal`, `RiskAssessmentRequest`, `RiskAssessmentResponse`.
- Client: `VoiceIntegrityClient.assess` method.
- Custom exceptions: `VoiceIntegrityError`, `APIError`, `ConnectionError`.
