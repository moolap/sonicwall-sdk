package tech.gandiva.sonicwall.internal;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Flexible JSON map helpers (mirrors Go {@code map[string]any} parsing). */
public final class JsonMaps {
  private JsonMaps() {}

  @SuppressWarnings("unchecked")
  public static Map<String, Object> asMap(Object value) {
    if (value instanceof Map<?, ?> map) {
      return (Map<String, Object>) map;
    }
    return Map.of();
  }

  public static String stringFromAny(Object value) {
    if (value == null) {
      return "";
    }
    if (value instanceof String s) {
      return s;
    }
    if (value instanceof Number n) {
      return String.valueOf(n.longValue());
    }
    if (value instanceof Boolean b) {
      return Boolean.toString(b);
    }
    return String.valueOf(value);
  }

  public static boolean boolFromAny(Object value, boolean defaultValue) {
    if (value == null) {
      return defaultValue;
    }
    if (value instanceof Boolean b) {
      return b;
    }
    return defaultValue;
  }

  public static Integer intFromAny(Object value) {
    if (value == null) {
      return null;
    }
    if (value instanceof Number n) {
      return n.intValue();
    }
    return null;
  }

  @SuppressWarnings("unchecked")
  public static List<Map<String, Object>> listOfMaps(Object raw) {
    if (!(raw instanceof List<?> list)) {
      return List.of();
    }
    List<Map<String, Object>> out = new ArrayList<>();
    for (Object item : list) {
      if (item instanceof Map<?, ?> map) {
        out.add((Map<String, Object>) map);
      }
    }
    return out;
  }
}
