package models

import (
	"fmt"
	"strconv"
)

// RuleAddress is a source or destination address for an access rule.
type RuleAddress struct {
	Any   bool
	Name  string
	Group string
}

// RuleService is a service matcher for an access rule.
type RuleService struct {
	Any  bool
	Name string
}

// RulePriority controls SonicOS rule ordering.
type RulePriority struct {
	Auto  bool
	Value *int
}

// AccessRule is an IPv4 access rule.
type AccessRule struct {
	Name                string
	FromZone            string
	ToZone              string
	Action              string // allow, deny, discard
	Enabled             bool
	Log                 bool
	Priority            RulePriority
	SourceAddress       RuleAddress
	DestinationAddress  RuleAddress
	Service             RuleService
	Comment             string
}

func stringFromAny(v any) string {
	if v == nil {
		return ""
	}
	switch t := v.(type) {
	case string:
		return t
	case float64:
		return strconv.FormatInt(int64(t), 10)
	case bool:
		return strconv.FormatBool(t)
	default:
		return fmt.Sprint(t)
	}
}

func boolFromAny(v any, defaultVal bool) bool {
	if v == nil {
		return defaultVal
	}
	b, ok := v.(bool)
	if !ok {
		return defaultVal
	}
	return b
}

// AccessRuleToAPIEnvelope returns {"access_rule":{"ipv4":{...}}}.
func AccessRuleToAPIEnvelope(r *AccessRule) map[string]any {
	inner := map[string]any{
		"from":        r.FromZone,
		"to":          r.ToZone,
		"action":      r.Action,
		"enabled":     r.Enabled,
		"log":         r.Log,
		"source":      ruleAddrWire(r.SourceAddress),
		"destination": ruleAddrWire(r.DestinationAddress),
		"service":     ruleSvcWire(r.Service),
	}
	if r.Name != "" {
		inner["name"] = r.Name
	}
	if r.Priority.Auto {
		inner["priority"] = map[string]any{"auto": true}
	} else if r.Priority.Value != nil {
		inner["priority"] = map[string]any{"value": *r.Priority.Value}
	}
	if r.Comment != "" {
		inner["comment"] = r.Comment
	}
	return map[string]any{"access_rule": map[string]any{"ipv4": inner}}
}

func ruleAddrWire(a RuleAddress) map[string]any {
	if a.Any {
		return map[string]any{"address": map[string]any{"any": true}}
	}
	if a.Name != "" {
		return map[string]any{"address": map[string]any{"name": a.Name}}
	}
	if a.Group != "" {
		return map[string]any{"address": map[string]any{"group": a.Group}}
	}
	return map[string]any{"address": map[string]any{"any": true}}
}

func ruleSvcWire(s RuleService) map[string]any {
	if s.Any {
		return map[string]any{"any": true}
	}
	if s.Name != "" {
		return map[string]any{"name": s.Name}
	}
	return map[string]any{"any": true}
}

// AccessRuleFromAPIItem parses a list item or singular response into AccessRule.
func AccessRuleFromAPIItem(data map[string]any) (*AccessRule, error) {
	inner := data
	if ar, ok := data["access_rule"].(map[string]any); ok {
		inner = ar
	}
	if ipv4, ok := inner["ipv4"].(map[string]any); ok {
		inner = ipv4
	}

	r := &AccessRule{
		Name:     stringFromAny(inner["name"]),
		FromZone: stringFromAny(inner["from"]),
		ToZone:   stringFromAny(inner["to"]),
		Action:   stringFromAny(inner["action"]),
		Enabled:  boolFromAny(inner["enabled"], true),
		Log:      inner["log"] == true,
		Priority: RulePriority{Auto: true},
	}

	if p, ok := inner["priority"].(map[string]any); ok {
		if p["auto"] == true {
			r.Priority = RulePriority{Auto: true}
		} else if v, ok := p["value"].(float64); ok {
			vi := int(v)
			r.Priority = RulePriority{Auto: false, Value: &vi}
		}
	}

	if src, ok := inner["source"].(map[string]any); ok {
		if addr, ok := src["address"].(map[string]any); ok {
			r.SourceAddress = parseRuleAddr(addr)
		}
	}
	if dst, ok := inner["destination"].(map[string]any); ok {
		if addr, ok := dst["address"].(map[string]any); ok {
			r.DestinationAddress = parseRuleAddr(addr)
		}
	}
	if svc, ok := inner["service"].(map[string]any); ok {
		r.Service = parseRuleSvc(svc)
	}
	if r.Action == "" {
		r.Action = "allow"
	}
	r.Comment = stringFromAny(inner["comment"])
	return r, nil
}

func parseRuleAddr(addr map[string]any) RuleAddress {
	if addr["any"] == true {
		return RuleAddress{Any: true}
	}
	if n, ok := addr["name"].(string); ok && n != "" {
		return RuleAddress{Name: n}
	}
	if g, ok := addr["group"].(string); ok && g != "" {
		return RuleAddress{Group: g}
	}
	return RuleAddress{Any: true}
}

func parseRuleSvc(svc map[string]any) RuleService {
	if svc["any"] == true {
		return RuleService{Any: true}
	}
	if n, ok := svc["name"].(string); ok && n != "" {
		return RuleService{Name: n}
	}
	return RuleService{Any: true}
}
