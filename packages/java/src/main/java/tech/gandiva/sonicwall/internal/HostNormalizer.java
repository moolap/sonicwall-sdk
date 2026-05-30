package tech.gandiva.sonicwall.internal;

import java.net.URI;

public final class HostNormalizer {
  private HostNormalizer() {}

  public static String baseUrl(String host) {
    String h = host.strip();
    while (h.endsWith("/")) {
      h = h.substring(0, h.length() - 1);
    }
    String lower = h.toLowerCase();
    if (lower.startsWith("https://") || lower.startsWith("http://")) {
      URI uri = URI.create(h);
      String scheme = uri.getScheme();
      String authority = uri.getAuthority();
      if (authority == null || authority.isBlank()) {
        return h + "/api/sonicos";
      }
      return scheme + "://" + authority + "/api/sonicos";
    }
    int slash = h.indexOf('/');
    if (slash >= 0) {
      h = h.substring(0, slash);
    }
    return "https://" + h + "/api/sonicos";
  }
}
