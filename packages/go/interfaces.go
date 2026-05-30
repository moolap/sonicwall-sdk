package sonicwall

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"

	"github.com/moolap/sonicwall-sdk/go/models"
)

const interfacesBase = "/interfaces"

// InterfacesService provides read-only access to network interfaces.
type InterfacesService struct {
	client *Client
}

// List returns all interfaces.
func (s *InterfacesService) List(ctx context.Context) ([]*models.Interface, error) {
	data, err := s.client.request(ctx, "GET", interfacesBase, nil)
	if err != nil {
		return nil, err
	}
	var top map[string]any
	if err := json.Unmarshal(data, &top); err != nil {
		return nil, err
	}
	raw, ok := top["interfaces"].([]any)
	if !ok {
		return nil, nil
	}
	out := make([]*models.Interface, 0, len(raw))
	for _, it := range raw {
		m, ok := it.(map[string]any)
		if !ok {
			continue
		}
		iface, err := models.InterfaceFromAPIItem(m)
		if err != nil {
			continue
		}
		out = append(out, iface)
	}
	return out, nil
}

// Get returns one interface by name (e.g. X0).
func (s *InterfacesService) Get(ctx context.Context, name string) (*models.Interface, error) {
	path := fmt.Sprintf("%s/name/%s", interfacesBase, url.PathEscape(name))
	data, err := s.client.request(ctx, "GET", path, nil)
	if err != nil {
		return nil, err
	}
	var top map[string]any
	if err := json.Unmarshal(data, &top); err != nil {
		return nil, err
	}
	return models.InterfaceFromAPIItem(top)
}
