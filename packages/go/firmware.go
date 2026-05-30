package sonicwall

import (
	"errors"
	"strings"
)

// FirmwareLimitationReason classifies SonicOS firmware/API limitation messages.
type FirmwareLimitationReason string

const (
	FirmwareAPINotFound        FirmwareLimitationReason = "api_not_found"
	FirmwareEndpointIncomplete FirmwareLimitationReason = "endpoint_incomplete"
	FirmwareCommandNotFound    FirmwareLimitationReason = "command_not_found"
	FirmwareNonConfigMode      FirmwareLimitationReason = "non_config_mode"
)

// UnsupportedEndpointError is returned when SonicOS reports a missing or unusable endpoint.
type UnsupportedEndpointError struct {
	HTTPError
	Reason FirmwareLimitationReason
}

func (e *UnsupportedEndpointError) Error() string {
	return e.HTTPError.Error()
}

// firmwareLimitationReason returns a short reason when SonicOS indicates a firmware/API limitation.
func firmwareLimitationReason(statusCode int, message string) *FirmwareLimitationReason {
	msg := strings.ToLower(message)
	if strings.Contains(msg, "api not found") {
		r := FirmwareAPINotFound
		return &r
	}
	if strings.Contains(msg, "endpoint is incomplete") || (statusCode == 400 && strings.Contains(msg, "incomplete")) {
		r := FirmwareEndpointIncomplete
		return &r
	}
	if strings.Contains(msg, "command") && strings.Contains(msg, "not found") {
		r := FirmwareCommandNotFound
		return &r
	}
	if statusCode == 405 && strings.Contains(msg, "non config mode") {
		r := FirmwareNonConfigMode
		return &r
	}
	return nil
}

// IsFirmwareUnsupportedError reports whether err reflects a known firmware/API limitation.
func IsFirmwareUnsupportedError(err error) bool {
	var unsupported *UnsupportedEndpointError
	if errors.As(err, &unsupported) {
		return true
	}
	var httpErr *HTTPError
	if errors.As(err, &httpErr) {
		if firmwareLimitationReason(httpErr.StatusCode, httpErr.message) != nil {
			return true
		}
		if httpErr.ResponseBody != nil && len(httpErr.ResponseBody.Status.Info) > 0 {
			sonicosMsg := httpErr.ResponseBody.Status.Info[0].Message
			if firmwareLimitationReason(httpErr.StatusCode, sonicosMsg) != nil {
				return true
			}
		}
	}
	var base *SonicWallError
	if errors.As(err, &base) {
		return firmwareLimitationReason(0, base.message) != nil
	}
	return false
}
