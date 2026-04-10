package sonicwall

// normalizeGetFromPlural adapts a GET response that returns a plural array
// into a singular envelope shape expected by model parsers.
func normalizeGetFromPlural(
	response map[string]any,
	pluralKey, singularKey string,
	predicate func(map[string]any) bool,
) map[string]any {
	raw, ok := response[pluralKey]
	if !ok {
		return response
	}
	items, ok := raw.([]any)
	if !ok || len(items) == 0 {
		return response
	}

	var selected map[string]any
	if predicate != nil {
		for _, it := range items {
			m, ok := it.(map[string]any)
			if !ok {
				continue
			}
			if predicate(m) {
				selected = m
				break
			}
		}
	}
	if selected == nil {
		if m, ok := items[0].(map[string]any); ok {
			selected = m
		}
	}
	if selected == nil {
		return response
	}

	if inner, ok := selected[singularKey].(map[string]any); ok {
		return map[string]any{singularKey: inner}
	}
	return map[string]any{singularKey: selected}
}

// unwrapIPv4 returns the ipv4 inner object from a list item envelope.
func unwrapIPv4(item map[string]any, wrappedKey string) map[string]any {
	if w, ok := item[wrappedKey].(map[string]any); ok {
		if ipv4, ok := w["ipv4"].(map[string]any); ok {
			return ipv4
		}
		return w
	}
	if ipv4, ok := item["ipv4"].(map[string]any); ok {
		return ipv4
	}
	return nil
}
