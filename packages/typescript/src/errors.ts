/**
 * SonicWall SDK error hierarchy.
 *
 * All errors extend SonicWallError. HTTP-derived errors carry
 * statusCode, message, and the raw response body.
 */

import { firmwareLimitationReason } from "./firmwareReason.ts";

export interface SonicOSStatusInfo {
  level?: string;
  code?: number;
  message?: string;
}

export interface SonicOSResponseBody {
  status?: {
    success?: boolean;
    info?: SonicOSStatusInfo[];
  };
  [key: string]: unknown;
}

/** Base class for all SonicWall SDK errors. */
export class SonicWallError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SonicWallError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Raised when the API returns a non-successful HTTP status. */
export class SonicWallHTTPError extends SonicWallError {
  readonly statusCode: number;
  readonly responseBody: SonicOSResponseBody;

  constructor(
    statusCode: number,
    message: string,
    responseBody: SonicOSResponseBody = {}
  ) {
    super(`HTTP ${statusCode}: ${message}`);
    this.name = "SonicWallHTTPError";
    this.statusCode = statusCode;
    this.responseBody = responseBody;
    Object.setPrototypeOf(this, new.target.prototype);
  }

  /** SonicOS internal error code from the response body, if present. */
  get sonicosCode(): number | undefined {
    return this.responseBody.status?.info?.[0]?.code;
  }

  /** SonicOS error message from the response body, if present. */
  get sonicosMessage(): string | undefined {
    return this.responseBody.status?.info?.[0]?.message;
  }
}

/** Raised when authentication fails. */
export class AuthenticationError extends SonicWallHTTPError {
  constructor(
    statusCode: number,
    message: string,
    responseBody: SonicOSResponseBody = {}
  ) {
    super(statusCode, message, responseBody);
    this.name = "AuthenticationError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Raised when the SonicOS session has expired. */
export class SessionExpiredError extends AuthenticationError {
  static readonly SESSION_EXPIRED_CODE = 1085;

  constructor(responseBody: SonicOSResponseBody = {}) {
    super(401, "SonicOS session has expired", responseBody);
    this.name = "SessionExpiredError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Raised when the authenticated user lacks permission. */
export class AuthorizationError extends SonicWallHTTPError {
  constructor(responseBody: SonicOSResponseBody = {}) {
    super(403, "Insufficient permissions", responseBody);
    this.name = "AuthorizationError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Raised when the requested resource is not found. */
export class NotFoundError extends SonicWallHTTPError {
  constructor(
    message = "Resource not found",
    responseBody: SonicOSResponseBody = {}
  ) {
    super(404, message, responseBody);
    this.name = "NotFoundError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Raised when a resource with the same name already exists. */
export class ConflictError extends SonicWallHTTPError {
  constructor(
    message = "Resource already exists",
    responseBody: SonicOSResponseBody = {}
  ) {
    super(409, message, responseBody);
    this.name = "ConflictError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Raised when committing pending configuration fails. */
export class CommitError extends SonicWallError {
  override readonly cause: Error | undefined;

  constructor(message: string, cause?: Error) {
    super(message);
    this.name = "CommitError";
    this.cause = cause;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Raised when rolling back pending configuration fails. */
export class RollbackError extends SonicWallError {
  override readonly cause: Error | undefined;

  constructor(message: string, cause?: Error) {
    super(message);
    this.name = "RollbackError";
    this.cause = cause;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Raised when the network connection fails. */
export class ConnectionError extends SonicWallError {
  constructor(message: string) {
    super(message);
    this.name = "ConnectionError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Raised when SonicOS reports an endpoint missing or unusable on this firmware. */
export class UnsupportedEndpointError extends SonicWallHTTPError {
  readonly reason: string;

  constructor(
    statusCode: number,
    message: string,
    reason: string,
    responseBody: SonicOSResponseBody = {}
  ) {
    super(statusCode, message, responseBody);
    this.name = "UnsupportedEndpointError";
    this.reason = reason;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

// SonicOS internal codes
export const SONICOS_CODE_NOT_FOUND = 1030;
export const SONICOS_CODE_ALREADY_EXISTS = 1055;

/**
 * Parse a SonicOS response body and raise a typed error if appropriate.
 * Returns void if the response is successful.
 */
export function raiseForSonicOSBody(
  statusCode: number,
  body: SonicOSResponseBody
): void {
  const status = body.status;
  if (!status) return;
  if (status.success === true) return;

  const code = status.info?.[0]?.code;
  const message = status.info?.[0]?.message ?? "Unknown error";

  if (code === SessionExpiredError.SESSION_EXPIRED_CODE) {
    throw new SessionExpiredError(body);
  }
  if (code === SONICOS_CODE_NOT_FOUND) {
    throw new NotFoundError(message, body);
  }
  if (code === SONICOS_CODE_ALREADY_EXISTS) {
    throw new ConflictError(message, body);
  }

  if (statusCode === 401) {
    throw new AuthenticationError(401, message, body);
  }
  if (statusCode === 403) {
    throw new AuthorizationError(body);
  }
  if (statusCode === 404) {
    throw new NotFoundError(message, body);
  }
  if (statusCode === 409) {
    throw new ConflictError(message, body);
  }

  throw mapHttpError(statusCode, message, body);
}

function mapHttpError(
  statusCode: number,
  message: string,
  body: SonicOSResponseBody
): SonicWallHTTPError {
  const reason = firmwareLimitationReason(statusCode, message);
  if (reason !== null) {
    return new UnsupportedEndpointError(statusCode, message, reason, body);
  }
  return new SonicWallHTTPError(statusCode, message, body);
}