package sonicwall

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"strings"

	"github.com/gandiva-tech/sonicwall-sdk/go/models"
)

const accessRulesBase = "/access-rules/ipv4"

// AccessRulesService provides CRUD for IPv4 access rules.
type AccessRulesService struct {
	client *Client
}

func isAccessRulesSchemaArrayErr(err error) bool {
	if err == nil {
		return false
	}
	msg := strings.ToLower(err.Error())
	return strings.Contains(msg, "schema validation error") &&
		strings.Contains(msg, "access_rules") &&
		strings.Contains(msg, "expected '['")
}

func accessRuleCollectionPayload(rule *models.AccessRule) map[string]any {
	env := models.AccessRuleToAPIEnvelope(rule)
	item := env["access_rule"]
	return map[string]any{"access_rules": []any{item}}
}

// List returns all IPv4 access rules.
func (s *AccessRulesService) List(ctx context.Context) ([]*models.AccessRule, error) {
	data, err := s.client.request(ctx, "GET", accessRulesBase, nil)
	if err != nil {
		return nil, err
	}
	var top map[string]any
	if err := json.Unmarshal(data, &top); err != nil {
		return nil, err
	}
	raw, ok := top["access_rules"].([]any)
	if !ok {
		return nil, nil
	}
	out := make([]*models.AccessRule, 0, len(raw))
	for _, it := range raw {
		m, ok := it.(map[string]any)
		if !ok {
			continue
		}
		r, err := models.AccessRuleFromAPIItem(m)
		if err != nil {
			continue
		}
		out = append(out, r)
	}
	return out, nil
}

// Get returns an access rule by zone pair and name.
func (s *AccessRulesService) Get(ctx context.Context, fromZone, toZone, name string) (*models.AccessRule, error) {
	path := fmt.Sprintf("%s/from/%s/to/%s/name/%s",
		accessRulesBase,
		url.PathEscape(fromZone),
		url.PathEscape(toZone),
		url.PathEscape(name),
	)
	data, err := s.client.request(ctx, "GET", path, nil)
	if err == nil {
		var top map[string]any
		if err := json.Unmarshal(data, &top); err != nil {
			return nil, err
		}
		norm := normalizeGetFromPlural(top, "access_rules", "access_rule", func(item map[string]any) bool {
			ipv4 := unwrapIPv4(item, "access_rule")
			if ipv4 == nil {
				return false
			}
			return ipv4["from"] == fromZone && ipv4["to"] == toZone && ipv4["name"] == name
		})
		return models.AccessRuleFromAPIItem(norm)
	}

	if !IsNotFound(err) {
		return nil, err
	}

	rules, err := s.List(ctx)
	if err != nil {
		return nil, err
	}
	for _, r := range rules {
		if r.FromZone == fromZone && r.ToZone == toZone && r.Name == name {
			return r, nil
		}
	}
	return nil, &NotFoundError{HTTPError{
		StatusCode: 404,
		SonicWallError: SonicWallError{
			message: fmt.Sprintf("access rule not found: %s->%s:%s", fromZone, toZone, name),
		},
	}}
}

// Create creates an access rule.
func (s *AccessRulesService) Create(ctx context.Context, rule *models.AccessRule) (*models.AccessRule, error) {
	payload := models.AccessRuleToAPIEnvelope(rule)
	if err := s.client.post(ctx, accessRulesBase, payload, nil); err != nil {
		if !isAccessRulesSchemaArrayErr(err) {
			return nil, err
		}
		if err := s.client.post(ctx, accessRulesBase, accessRuleCollectionPayload(rule), nil); err != nil {
			return nil, err
		}
	}
	if rule.Name != "" {
		got, gErr := s.Get(ctx, rule.FromZone, rule.ToZone, rule.Name)
		if gErr == nil {
			return got, nil
		}
	}
	return rule, nil
}

// Update replaces an access rule.
func (s *AccessRulesService) Update(ctx context.Context, fromZone, toZone, name string, rule *models.AccessRule) (*models.AccessRule, error) {
	path := fmt.Sprintf("%s/from/%s/to/%s/name/%s",
		accessRulesBase,
		url.PathEscape(fromZone),
		url.PathEscape(toZone),
		url.PathEscape(name),
	)
	payload := models.AccessRuleToAPIEnvelope(rule)
	if err := s.client.put(ctx, path, payload, nil); err != nil {
		if !isAccessRulesSchemaArrayErr(err) {
			return nil, err
		}
		if err := s.client.put(ctx, path, accessRuleCollectionPayload(rule), nil); err != nil {
			return nil, err
		}
	}
	effective := rule.Name
	if effective == "" {
		effective = name
	}
	got, gErr := s.Get(ctx, rule.FromZone, rule.ToZone, effective)
	if gErr == nil {
		return got, nil
	}
	return rule, nil
}

// Delete removes an access rule.
func (s *AccessRulesService) Delete(ctx context.Context, fromZone, toZone, name string) error {
	path := fmt.Sprintf("%s/from/%s/to/%s/name/%s",
		accessRulesBase,
		url.PathEscape(fromZone),
		url.PathEscape(toZone),
		url.PathEscape(name),
	)
	return s.client.del(ctx, path)
}

// InsertBefore creates a rule ordered before an existing rule (when priorities are numeric).
func (s *AccessRulesService) InsertBefore(ctx context.Context, rule *models.AccessRule, beforeName string) (*models.AccessRule, error) {
	r := *rule
	if target, err := s.Get(ctx, r.FromZone, r.ToZone, beforeName); err == nil {
		if !target.Priority.Auto && target.Priority.Value != nil {
			v := *target.Priority.Value
			r.Priority = models.RulePriority{Auto: false, Value: &v}
		}
	}
	return s.Create(ctx, &r)
}

// InsertAfter creates a rule ordered after an existing rule (when priorities are numeric).
func (s *AccessRulesService) InsertAfter(ctx context.Context, rule *models.AccessRule, afterName string) (*models.AccessRule, error) {
	r := *rule
	if target, err := s.Get(ctx, r.FromZone, r.ToZone, afterName); err == nil {
		if !target.Priority.Auto && target.Priority.Value != nil {
			v := *target.Priority.Value + 1
			r.Priority = models.RulePriority{Auto: false, Value: &v}
		}
	}
	return s.Create(ctx, &r)
}
