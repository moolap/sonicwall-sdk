package sonicwall

import "testing"

func TestFirmwareLimitationReason(t *testing.T) {
	tests := []struct {
		status  int
		message string
		want    FirmwareLimitationReason
	}{
		{404, "API not found", FirmwareAPINotFound},
		{400, "API endpoint is incomplete", FirmwareEndpointIncomplete},
		{400, "incomplete", FirmwareEndpointIncomplete},
		{404, "command xyz not found", FirmwareCommandNotFound},
		{405, "Non config mode", FirmwareNonConfigMode},
	}
	for _, tt := range tests {
		got := firmwareLimitationReason(tt.status, tt.message)
		if got == nil || *got != tt.want {
			t.Errorf("firmwareLimitationReason(%d, %q) = %v, want %q", tt.status, tt.message, got, tt.want)
		}
	}
	if firmwareLimitationReason(500, "Internal server error") != nil {
		t.Error("expected nil for generic 500")
	}
}

func TestNewHTTPErrorUnsupportedEndpoint(t *testing.T) {
	body := &SonicOSErrorResponse{
		Status: SonicOSStatus{
			Success: false,
			Info: []SonicOSStatusInfo{{
				Code:    400,
				Message: "API endpoint is incomplete",
			}},
		},
	}
	err := newHTTPError(400, body)
	if !IsUnsupportedEndpoint(err) {
		t.Fatalf("expected UnsupportedEndpointError, got %T", err)
	}
	ue := err.(*UnsupportedEndpointError)
	if ue.Reason != FirmwareEndpointIncomplete {
		t.Fatalf("reason = %q, want %q", ue.Reason, FirmwareEndpointIncomplete)
	}
}
