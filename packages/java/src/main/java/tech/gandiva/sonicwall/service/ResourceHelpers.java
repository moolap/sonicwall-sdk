package tech.gandiva.sonicwall.service;

import com.fasterxml.jackson.core.type.TypeReference;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import tech.gandiva.sonicwall.exception.NotFoundException;
import tech.gandiva.sonicwall.internal.ApiTransport;

final class ResourceHelpers {
  private ResourceHelpers() {}

  static String encode(String value) {
    return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20");
  }

  static boolean isNotFound(RuntimeException ex) {
    return ex instanceof NotFoundException;
  }

  static Map<String, Object> readTopMap(ApiTransport transport, byte[] data) {
    return transport.readValue(data, new TypeReference<Map<String, Object>>() {});
  }

  static boolean isSchemaArrayError(RuntimeException ex, String collectionKey) {
    String msg = ex.getMessage() == null ? "" : ex.getMessage().toLowerCase();
    return msg.contains("schema validation error")
        && msg.contains(collectionKey)
        && msg.contains("expected '['");
  }
}
