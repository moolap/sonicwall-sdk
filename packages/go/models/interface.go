package models

// Interface is a SonicOS network interface (read-only SDK view).
type Interface struct {
	Name         string
	IPAssignment string
	IP           string
	Subnet       string
	Zone         string
	Enabled      bool
	Comment      string
}

// InterfaceFromAPIItem parses interface from GET response.
func InterfaceFromAPIItem(data map[string]any) (*Interface, error) {
	inner := data
	if w, ok := data["interface"].(map[string]any); ok {
		inner = w
	}
	return &Interface{
		Name:         stringFromAny(inner["name"]),
		IPAssignment: stringFromAny(inner["ip_assignment"]),
		IP:           stringFromAny(inner["ip"]),
		Subnet:       stringFromAny(inner["subnet"]),
		Zone:         stringFromAny(inner["zone"]),
		Enabled:      boolFromAny(inner["enabled"], true),
		Comment:      stringFromAny(inner["comment"]),
	}, nil
}
