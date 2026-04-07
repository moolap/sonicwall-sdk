package sonicwall

import (
	"errors"
	"fmt"
)

// SonicOSStatusInfo is a single entry in the SonicOS status info array.
type SonicOSStatusInfo struct {
	Level   string `json:"level"`
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// SonicOSStatus is the status block returned in every SonicOS API response.
type SonicOSStatus struct {
	Success bool                `json:"success"`
	Info    []SonicOSStatusInfo `json:"info"`
}

// SonicOSErrorResponse is the minimal shape of an error response body.
type SonicOSErrorResponse struct {
	Status SonicOSStatus `json:"status"`
}

// SonicOS internal status codes.
const (
	SonicOSCodeNotFound      = 1030
	SonicOSCodeAlreadyExists = 1055
	SonicOSCodeSessionExpired = 1085
)

// SonicWallError is the base error type for all SDK errors.
type SonicWallError struct {
	message string
}

func (e *SonicWallError) Error() string {
	return e.message
}

// HTTPError is returned when the SonicOS API returns a non-successful response.
type HTTPError struct {
	SonicWallError
	StatusCode   int
	SonicOSCode  int
	ResponseBody *SonicOSErrorResponse
}

func (e *HTTPError) Error() string {
	if e.SonicOSCode != 0 && e.ResponseBody != nil {
		msg := ""
		if len(e.ResponseBody.Status.Info) > 0 {
			msg = e.ResponseBody.Status.Info[0].Message
		}
		return fmt.Sprintf("HTTP %d (SonicOS %d): %s", e.StatusCode, e.SonicOSCode, msg)
	}
	return fmt.Sprintf("HTTP %d: %s", e.StatusCode, e.message)
}

// NotFoundError is returned when the requested resource does not exist.
type NotFoundError struct {
	HTTPError
}

// ConflictError is returned when a resource with the same name already exists.
type ConflictError struct {
	HTTPError
}

// AuthenticationError is returned when credentials are invalid or the session has expired.
type AuthenticationError struct {
	HTTPError
}

// SessionExpiredError is returned when the SonicOS session has expired.
type SessionExpiredError struct {
	AuthenticationError
}

// AuthorizationError is returned when the user lacks permission for the operation.
type AuthorizationError struct {
	HTTPError
}

// CommitError is returned when committing pending changes fails.
type CommitError struct {
	SonicWallError
	Cause error
}

func (e *CommitError) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("commit failed: %v", e.Cause)
	}
	return "commit failed: " + e.message
}

func (e *CommitError) Unwrap() error { return e.Cause }

// RollbackError is returned when rolling back pending changes fails.
type RollbackError struct {
	SonicWallError
	Cause error
}

func (e *RollbackError) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("rollback failed: %v", e.Cause)
	}
	return "rollback failed: " + e.message
}

func (e *RollbackError) Unwrap() error { return e.Cause }

// ConnectionError is returned when a network connection cannot be established.
type ConnectionError struct {
	SonicWallError
	Cause error
}

func (e *ConnectionError) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("connection error: %v", e.Cause)
	}
	return "connection error: " + e.message
}

func (e *ConnectionError) Unwrap() error { return e.Cause }

// Helper functions to check error types.

// IsNotFound returns true if the error is a NotFoundError.
func IsNotFound(err error) bool {
	var target *NotFoundError
	return errors.As(err, &target)
}

// IsConflict returns true if the error is a ConflictError.
func IsConflict(err error) bool {
	var target *ConflictError
	return errors.As(err, &target)
}

// IsUnauthorized returns true if the error is an AuthenticationError or SessionExpiredError.
func IsUnauthorized(err error) bool {
	var auth *AuthenticationError
	var session *SessionExpiredError
	return errors.As(err, &auth) || errors.As(err, &session)
}

// IsSessionExpired returns true if the error indicates a SonicOS session expiry.
func IsSessionExpired(err error) bool {
	var target *SessionExpiredError
	return errors.As(err, &target)
}

// newHTTPError creates the appropriate typed error from a status code and SonicOS response body.
func newHTTPError(statusCode int, body *SonicOSErrorResponse) error {
	base := HTTPError{
		StatusCode:   statusCode,
		ResponseBody: body,
	}

	if body != nil && len(body.Status.Info) > 0 {
		base.SonicOSCode = body.Status.Info[0].Code
		base.SonicWallError.message = body.Status.Info[0].Message
	}

	if base.SonicOSCode == SonicOSCodeSessionExpired {
		return &SessionExpiredError{AuthenticationError{base}}
	}
	if base.SonicOSCode == SonicOSCodeNotFound {
		return &NotFoundError{base}
	}
	if base.SonicOSCode == SonicOSCodeAlreadyExists {
		return &ConflictError{base}
	}

	switch statusCode {
	case 401:
		if base.SonicOSCode == SonicOSCodeSessionExpired {
			return &SessionExpiredError{AuthenticationError{base}}
		}
		return &AuthenticationError{base}
	case 403:
		return &AuthorizationError{base}
	case 404:
		return &NotFoundError{base}
	case 409:
		return &ConflictError{base}
	}

	if base.message == "" {
		base.message = fmt.Sprintf("unexpected status %d", statusCode)
	}
	return &base
}