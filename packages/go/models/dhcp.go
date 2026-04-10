package models

// DhcpLease is an active DHCP lease (read-only).
type DhcpLease struct {
	IP        string
	MAC       string
	Hostname  string
	Expires   string
	Interface string
}

// DhcpLeaseFromMap parses a lease row from the DHCP API.
func DhcpLeaseFromMap(data map[string]any) (*DhcpLease, error) {
	return &DhcpLease{
		IP:        stringFromAny(data["ip"]),
		MAC:       stringFromAny(data["mac"]),
		Hostname:  stringFromAny(data["hostname"]),
		Expires:   stringFromAny(data["expires"]),
		Interface: stringFromAny(data["interface"]),
	}, nil
}
