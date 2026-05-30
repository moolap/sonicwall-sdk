package tech.gandiva.sonicwall.service;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/** Read-only list helpers for resources with flexible SonicOS JSON shapes. */
final class JsonResourceParser {
  private JsonResourceParser() {}

  static List<JsonNode> listItems(JsonNode root, String collectionKey) {
    JsonNode arr = root.get(collectionKey);
    List<JsonNode> out = new ArrayList<>();
    if (arr == null || !arr.isArray()) {
      return out;
    }
    for (JsonNode item : arr) {
      out.add(item);
    }
    return out;
  }

  static JsonNode ipv4Node(JsonNode item) {
    Iterator<String> fields = item.fieldNames();
    while (fields.hasNext()) {
      String key = fields.next();
      JsonNode nested = item.get(key);
      if (nested != null && nested.has("ipv4")) {
        return nested.get("ipv4");
      }
      if (nested != null && nested.has("name")) {
        return nested;
      }
    }
    return item;
  }
}
