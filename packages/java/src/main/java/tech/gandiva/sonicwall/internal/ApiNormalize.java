package tech.gandiva.sonicwall.internal;

import java.util.List;
import java.util.Map;
import java.util.function.Predicate;

/** Adapts plural GET responses into singular envelopes for model parsers. */
public final class ApiNormalize {
  private ApiNormalize() {}

  public static Map<String, Object> normalizeGetFromPlural(
      Map<String, Object> response,
      String pluralKey,
      String singularKey,
      Predicate<Map<String, Object>> predicate) {
    Object raw = response.get(pluralKey);
    if (!(raw instanceof List<?> items) || items.isEmpty()) {
      return response;
    }

    Map<String, Object> selected = null;
    if (predicate != null) {
      for (Object item : items) {
        Map<String, Object> map = JsonMaps.asMap(item);
        if (!map.isEmpty() && predicate.test(map)) {
          selected = map;
          break;
        }
      }
    }
    if (selected == null) {
      selected = JsonMaps.asMap(items.get(0));
    }
    if (selected.isEmpty()) {
      return response;
    }

    Object inner = selected.get(singularKey);
    if (inner instanceof Map<?, ?>) {
      return Map.of(singularKey, inner);
    }
    return Map.of(singularKey, selected);
  }

  public static Map<String, Object> unwrapIPv4(Map<String, Object> item, String wrappedKey) {
    Map<String, Object> wrapped = JsonMaps.asMap(item.get(wrappedKey));
    if (!wrapped.isEmpty()) {
      Map<String, Object> ipv4 = JsonMaps.asMap(wrapped.get("ipv4"));
      return ipv4.isEmpty() ? wrapped : ipv4;
    }
    Map<String, Object> ipv4 = JsonMaps.asMap(item.get("ipv4"));
    return ipv4.isEmpty() ? null : ipv4;
  }
}
