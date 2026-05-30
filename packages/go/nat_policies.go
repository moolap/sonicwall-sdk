package sonicwall

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"strings"

	"github.com/moolap/sonicwall-sdk/go/models"
)

const natPoliciesBase = "/nat-policies/ipv4"

// NatPoliciesService provides CRUD for IPv4 NAT policies.
type NatPoliciesService struct {
	client *Client
}

func isNatPoliciesSchemaArrayErr(err error) bool {
	if err == nil {
		return false
	}
	msg := strings.ToLower(err.Error())
	return strings.Contains(msg, "schema validation error") &&
		strings.Contains(msg, "nat_policies") &&
		strings.Contains(msg, "expected '['")
}

// List returns all IPv4 NAT policies.
func (s *NatPoliciesService) List(ctx context.Context) ([]*models.NatPolicy, error) {
	data, err := s.client.request(ctx, "GET", natPoliciesBase, nil)
	if err != nil {
		return nil, err
	}
	var top map[string]any
	if err := json.Unmarshal(data, &top); err != nil {
		return nil, err
	}
	raw, ok := top["nat_policies"].([]any)
	if !ok {
		return nil, nil
	}
	out := make([]*models.NatPolicy, 0, len(raw))
	for _, it := range raw {
		m, ok := it.(map[string]any)
		if !ok {
			continue
		}
		p, err := models.NatPolicyFromAPIItem(m)
		if err != nil {
			continue
		}
		out = append(out, p)
	}
	return out, nil
}

// Get returns a NAT policy by name.
func (s *NatPoliciesService) Get(ctx context.Context, name string) (*models.NatPolicy, error) {
	path := fmt.Sprintf("%s/name/%s", natPoliciesBase, url.PathEscape(name))
	data, err := s.client.request(ctx, "GET", path, nil)
	if err == nil {
		var top map[string]any
		if err := json.Unmarshal(data, &top); err != nil {
			return nil, err
		}
		norm := normalizeGetFromPlural(top, "nat_policies", "nat_policy", func(item map[string]any) bool {
			ipv4 := unwrapIPv4(item, "nat_policy")
			if ipv4 == nil {
				return false
			}
			return ipv4["name"] == name
		})
		return models.NatPolicyFromAPIItem(norm)
	}

	if !IsNotFound(err) {
		return nil, err
	}

	list, err := s.List(ctx)
	if err != nil {
		return nil, err
	}
	for _, p := range list {
		if p.Name == name {
			return p, nil
		}
	}
	return nil, &NotFoundError{HTTPError{
		StatusCode:     404,
		SonicWallError: SonicWallError{message: "NAT policy not found: " + name},
	}}
}

// Create creates a NAT policy.
func (s *NatPoliciesService) Create(ctx context.Context, policy *models.NatPolicy) (*models.NatPolicy, error) {
	payload := models.NatPolicyToAPIEnvelope(policy)
	if err := s.client.post(ctx, natPoliciesBase, payload, nil); err != nil {
		if !isNatPoliciesSchemaArrayErr(err) {
			return nil, err
		}
		if err := s.client.post(ctx, natPoliciesBase, models.NatPolicyCollectionPayload(policy), nil); err != nil {
			if err2 := s.client.post(ctx, natPoliciesBase, models.NatPolicyFirmwareCollectionPayload(policy), nil); err2 != nil {
				return nil, err2
			}
		}
	}
	if policy.Name != "" {
		got, gErr := s.Get(ctx, policy.Name)
		if gErr == nil {
			return got, nil
		}
	}
	return policy, nil
}

// Update updates a NAT policy and returns the latest representation when possible.
func (s *NatPoliciesService) Update(ctx context.Context, name string, policy *models.NatPolicy) (*models.NatPolicy, error) {
	path := fmt.Sprintf("%s/name/%s", natPoliciesBase, url.PathEscape(name))
	payload := models.NatPolicyToAPIEnvelope(policy)
	if err := s.client.put(ctx, path, payload, nil); err != nil {
		if !isNatPoliciesSchemaArrayErr(err) {
			return nil, err
		}
		if err := s.client.put(ctx, path, models.NatPolicyCollectionPayload(policy), nil); err != nil {
			if err2 := s.client.put(ctx, path, models.NatPolicyFirmwareCollectionPayload(policy), nil); err2 != nil {
				return nil, err2
			}
		}
	}
	effective := policy.Name
	if effective == "" {
		effective = name
	}
	got, err := s.Get(ctx, effective)
	if err == nil {
		return got, nil
	}
	return policy, nil
}

// Delete removes a NAT policy.
func (s *NatPoliciesService) Delete(ctx context.Context, name string) error {
	path := fmt.Sprintf("%s/name/%s", natPoliciesBase, url.PathEscape(name))
	return s.client.del(ctx, path)
}

// Ensure creates or updates a NAT policy by name.
func (s *NatPoliciesService) Ensure(ctx context.Context, policy *models.NatPolicy) (*models.NatPolicy, bool, error) {
	if policy.Name == "" {
		created, err := s.Create(ctx, policy)
		return created, true, err
	}
	_, err := s.Get(ctx, policy.Name)
	if err != nil {
		if IsNotFound(err) {
			created, cErr := s.Create(ctx, policy)
			return created, true, cErr
		}
		return nil, false, err
	}
	updated, err := s.Update(ctx, policy.Name, policy)
	return updated, false, err
}
