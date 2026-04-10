package models

// PortRange is a TCP/UDP port range.
type PortRange struct {
	Begin int
	End   int
}

// IcmpSpec describes ICMP type/code.
type IcmpSpec struct {
	Type int
	Code int
}

// ServiceProtocol holds one or more protocol specs.
type ServiceProtocol struct {
	TCP  *PortRange
	UDP  *PortRange
	ICMP *IcmpSpec
}

// ServiceObject is a reusable service definition.
type ServiceObject struct {
	Name     string
	Protocol ServiceProtocol
}

func intFromAny(v any) (int, bool) {
	switch t := v.(type) {
	case float64:
		return int(t), true
	case int:
		return t, true
	case int64:
		return int(t), true
	default:
		return 0, false
	}
}

// ServiceObjectToAPIEnvelope returns {"service_object":{...}}.
func ServiceObjectToAPIEnvelope(o *ServiceObject) map[string]any {
	proto := map[string]any{}
	if o.Protocol.TCP != nil {
		proto["tcp"] = map[string]any{"begin": o.Protocol.TCP.Begin, "end": o.Protocol.TCP.End}
	}
	if o.Protocol.UDP != nil {
		proto["udp"] = map[string]any{"begin": o.Protocol.UDP.Begin, "end": o.Protocol.UDP.End}
	}
	if o.Protocol.ICMP != nil {
		proto["icmp"] = map[string]any{"type": o.Protocol.ICMP.Type, "code": o.Protocol.ICMP.Code}
	}
	return map[string]any{
		"service_object": map[string]any{
			"name":     o.Name,
			"protocol": proto,
		},
	}
}

// ServiceObjectFirmwareCollectionPayload is the flat firmware variant.
func ServiceObjectFirmwareCollectionPayload(o *ServiceObject) map[string]any {
	row := map[string]any{"name": o.Name}
	if o.Protocol.TCP != nil {
		row["tcp"] = map[string]any{"begin": o.Protocol.TCP.Begin, "end": o.Protocol.TCP.End}
	}
	if o.Protocol.UDP != nil {
		row["udp"] = map[string]any{"begin": o.Protocol.UDP.Begin, "end": o.Protocol.UDP.End}
	}
	if o.Protocol.ICMP != nil {
		row["icmp"] = map[string]any{"type": o.Protocol.ICMP.Type, "code": o.Protocol.ICMP.Code}
	}
	return map[string]any{"service_objects": []map[string]any{row}}
}

// ServiceObjectCollectionPayload wraps as service_objects array of inner objects.
func ServiceObjectCollectionPayload(o *ServiceObject) map[string]any {
	env := ServiceObjectToAPIEnvelope(o)
	inner := env["service_object"]
	return map[string]any{"service_objects": []any{inner}}
}

// ServiceObjectFromAPIItem parses a service object from API data.
func ServiceObjectFromAPIItem(data map[string]any) (*ServiceObject, error) {
	inner := data
	if so, ok := data["service_object"].(map[string]any); ok {
		inner = so
	}
	o := &ServiceObject{Name: stringFromAny(inner["name"])}
	rawProto, _ := inner["protocol"].(map[string]any)
	if rawProto == nil {
		rawProto = map[string]any{}
	}
	if tcp, ok := rawProto["tcp"].(map[string]any); ok {
		b, _ := intFromAny(tcp["begin"])
		e, _ := intFromAny(tcp["end"])
		o.Protocol.TCP = &PortRange{Begin: b, End: e}
	}
	if udp, ok := rawProto["udp"].(map[string]any); ok {
		b, _ := intFromAny(udp["begin"])
		e, _ := intFromAny(udp["end"])
		o.Protocol.UDP = &PortRange{Begin: b, End: e}
	}
	if icmp, ok := rawProto["icmp"].(map[string]any); ok {
		typ, _ := intFromAny(icmp["type"])
		code, okc := intFromAny(icmp["code"])
		if !okc {
			code = 0
		}
		o.Protocol.ICMP = &IcmpSpec{Type: typ, Code: code}
	}
	// Firmware flat shape on list items
	if o.Protocol.TCP == nil {
		if tcp, ok := inner["tcp"].(map[string]any); ok {
			b, _ := intFromAny(tcp["begin"])
			e, _ := intFromAny(tcp["end"])
			o.Protocol.TCP = &PortRange{Begin: b, End: e}
		}
	}
	if o.Protocol.UDP == nil {
		if udp, ok := inner["udp"].(map[string]any); ok {
			b, _ := intFromAny(udp["begin"])
			e, _ := intFromAny(udp["end"])
			o.Protocol.UDP = &PortRange{Begin: b, End: e}
		}
	}
	if o.Protocol.ICMP == nil {
		if icmp, ok := inner["icmp"].(map[string]any); ok {
			typ, _ := intFromAny(icmp["type"])
			code, okc := intFromAny(icmp["code"])
			if !okc {
				code = 0
			}
			o.Protocol.ICMP = &IcmpSpec{Type: typ, Code: code}
		}
	}
	return o, nil
}
