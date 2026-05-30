package sonicwall

import (
	"context"
	"encoding/json"

	"github.com/moolap/sonicwall-sdk/go/models"
)

var dhcpCandidatePaths = []string{
	"/dhcp/server/lease",
	"/dhcp/server/leases",
	"/dhcp/leases",
	"/dhcp-server/lease",
}

var dhcpCandidateKeys = []string{"dhcp_leases", "dhcp_server_leases", "leases"}

// DhcpService provides read access to DHCP leases.
type DhcpService struct {
	client *Client
}

// ListLeases returns active DHCP server leases, probing firmware path variants.
func (s *DhcpService) ListLeases(ctx context.Context) ([]*models.DhcpLease, error) {
	var lastNotFound error
	for _, path := range dhcpCandidatePaths {
		data, err := s.client.request(ctx, "GET", path, nil)
		if err != nil {
			if IsNotFound(err) {
				lastNotFound = err
				continue
			}
			return nil, err
		}
		var top map[string]any
		if err := json.Unmarshal(data, &top); err != nil {
			return nil, err
		}
		var items []any
		for _, key := range dhcpCandidateKeys {
			if raw, ok := top[key].([]any); ok {
				items = raw
				break
			}
		}
		if items == nil {
			if st, ok := top["status"].(map[string]any); ok && st["success"] == true {
				return nil, nil
			}
			return nil, nil
		}
		out := make([]*models.DhcpLease, 0, len(items))
		for _, it := range items {
			m, ok := it.(map[string]any)
			if !ok {
				continue
			}
			lease, err := models.DhcpLeaseFromMap(m)
			if err != nil {
				continue
			}
			out = append(out, lease)
		}
		return out, nil
	}
	if lastNotFound != nil {
		return nil, lastNotFound
	}
	return nil, nil
}
