package models

// NatPolicy is an IPv4 NAT policy.
type NatPolicy struct {
	Name                  string
	Enabled               bool
	InboundInterface      string
	OutboundInterface     string
	OriginalSource        string
	TranslatedSource      string
	OriginalDestination   string
	TranslatedDestination string
	OriginalService       string
	TranslatedService     string
	Comment               string
}

func normRef(value any, defaultVal string) string {
	if s, ok := value.(string); ok {
		return s
	}
	if m, ok := value.(map[string]any); ok {
		if m["any"] == true {
			return "any"
		}
		if m["original"] == true {
			return "original"
		}
		if n, ok := m["name"].(string); ok {
			return n
		}
		if g, ok := m["group"].(string); ok {
			return g
		}
	}
	return defaultVal
}

// NatPolicyToAPIEnvelope returns {"nat_policy":{"ipv4":{...}}}.
func NatPolicyToAPIEnvelope(p *NatPolicy) map[string]any {
	inner := map[string]any{
		"inbound_interface":      p.InboundInterface,
		"outbound_interface":     p.OutboundInterface,
		"original_source":        p.OriginalSource,
		"translated_source":      p.TranslatedSource,
		"original_destination":   p.OriginalDestination,
		"translated_destination": p.TranslatedDestination,
		"original_service":       p.OriginalService,
		"translated_service":     p.TranslatedService,
		"enabled":                p.Enabled,
	}
	if p.Name != "" {
		inner["name"] = p.Name
	}
	if p.Comment != "" {
		inner["comment"] = p.Comment
	}
	return map[string]any{"nat_policy": map[string]any{"ipv4": inner}}
}

func refObj(value string, allowOriginal bool) map[string]any {
	if value == "any" {
		return map[string]any{"any": true}
	}
	if allowOriginal && value == "original" {
		return map[string]any{"original": true}
	}
	return map[string]any{"name": value}
}

// NatPolicyFirmwareCollectionPayload is the alternate firmware POST shape.
func NatPolicyFirmwareCollectionPayload(p *NatPolicy) map[string]any {
	return map[string]any{
		"nat_policies": []map[string]any{
			{
				"ipv4": map[string]any{
					"name":                   p.Name,
					"inbound":                p.InboundInterface,
					"outbound":               p.OutboundInterface,
					"source":                 refObj(p.OriginalSource, false),
					"translated_source":      refObj(p.TranslatedSource, true),
					"destination":            refObj(p.OriginalDestination, false),
					"translated_destination": refObj(p.TranslatedDestination, true),
					"service":                refObj(p.OriginalService, false),
					"translated_service":     refObj(p.TranslatedService, true),
					"enable":                 p.Enabled,
					"comment":                p.Comment,
				},
			},
		},
	}
}

// NatPolicyCollectionPayload wraps a single policy as nat_policies array item.
func NatPolicyCollectionPayload(p *NatPolicy) map[string]any {
	env := NatPolicyToAPIEnvelope(p)
	item := env["nat_policy"]
	return map[string]any{"nat_policies": []any{item}}
}

// NatPolicyFromAPIItem parses NAT policy from list or singular response.
func NatPolicyFromAPIItem(data map[string]any) (*NatPolicy, error) {
	inner := data
	if np, ok := data["nat_policy"].(map[string]any); ok {
		inner = np
	}
	if ipv4, ok := inner["ipv4"].(map[string]any); ok {
		inner = ipv4
	}

	enabled := boolFromAny(inner["enabled"], true)
	if inner["enable"] == false {
		enabled = false
	}

	p := &NatPolicy{
		Name:                  stringFromAny(inner["name"]),
		Enabled:               enabled,
		InboundInterface:      stringFromAny(inner["inbound_interface"]),
		OutboundInterface:     stringFromAny(inner["outbound_interface"]),
		OriginalSource:        normRef(inner["original_source"], "any"),
		TranslatedSource:      normRef(inner["translated_source"], "original"),
		OriginalDestination:   normRef(inner["original_destination"], "any"),
		TranslatedDestination: normRef(inner["translated_destination"], "original"),
		OriginalService:       normRef(inner["original_service"], "any"),
		TranslatedService:     normRef(inner["translated_service"], "original"),
		Comment:               stringFromAny(inner["comment"]),
	}
	if p.InboundInterface == "" {
		p.InboundInterface = stringFromAny(inner["inbound"])
	}
	if p.OutboundInterface == "" {
		p.OutboundInterface = stringFromAny(inner["outbound"])
	}
	if p.OriginalSource == "" || p.OriginalSource == "any" {
		p.OriginalSource = normRef(inner["source"], "any")
	}
	if p.OriginalDestination == "" || p.OriginalDestination == "any" {
		p.OriginalDestination = normRef(inner["destination"], "any")
	}
	if p.OriginalService == "" || p.OriginalService == "any" {
		p.OriginalService = normRef(inner["service"], "any")
	}
	return p, nil
}
