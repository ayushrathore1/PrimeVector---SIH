/**
 * Custom errors for the Voice Integrity Node.js SDK.
 */

export class VoiceIntegrityError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "VoiceIntegrityError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class APIError extends VoiceIntegrityError {
  public readonly statusCode: number;
  public readonly responseBody?: string;

  constructor(statusCode: number, message: string, responseBody?: string) {
    super(`API Error ${statusCode}: ${message}`);
    this.name = "APIError";
    this.statusCode = statusCode;
    this.responseBody = responseBody;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ConnectionError extends VoiceIntegrityError {
  public readonly cause?: Error;

  constructor(message: string, cause?: Error) {
    super(`Connection Error: ${message}`);
    this.name = "ConnectionError";
    this.cause = cause;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
