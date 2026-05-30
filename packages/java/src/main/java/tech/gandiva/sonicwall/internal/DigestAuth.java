package tech.gandiva.sonicwall.internal;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** SonicOS 7.x Digest auth-int helpers (mirrors Python/TypeScript). */
public final class DigestAuth {
  private static final Pattern DIGEST_PARAM =
      Pattern.compile("(\\w+)=(?:\"([^\"]*?)\"|([^,\\s]+))");

  private DigestAuth() {}

  public static Map<String, String> parseDigestChallenge(String wwwAuth) {
    String body = wwwAuth.trim().replaceFirst("(?i)^[Dd]igest\\s+", "");
    Map<String, String> params = new HashMap<>();
    Matcher matcher = DIGEST_PARAM.matcher(body);
    while (matcher.find()) {
      String value = matcher.group(2);
      if (value == null) {
        value = matcher.group(3);
      }
      params.put(matcher.group(1), value == null ? "" : value);
    }
    return params;
  }

  public static Map<String, String> pickAuthIntChallenge(List<String> wwwAuthenticate) {
    List<Map<String, String>> candidates = new ArrayList<>();
    for (String value : wwwAuthenticate) {
      if (!value.toLowerCase().startsWith("digest")) {
        continue;
      }
      Map<String, String> parsed = parseDigestChallenge(value);
      if (parsed.getOrDefault("qop", "").contains("auth-int")) {
        candidates.add(parsed);
      }
    }
    if (candidates.isEmpty()) {
      return null;
    }
    return candidates.stream().min(Comparator.comparingInt(DigestAuth::priority)).orElse(null);
  }

  public static String buildDigestAuthHeader(
      String method,
      String url,
      byte[] body,
      String username,
      String password,
      Map<String, String> challenge) {
    String algorithm = challenge.getOrDefault("algorithm", "MD5").toUpperCase();
    String realm = challenge.getOrDefault("realm", "");
    String nonce = challenge.getOrDefault("nonce", "");
    String opaque = challenge.getOrDefault("opaque", "");

    URI uri = URI.create(url);
    String uriPath = uri.getRawPath();
    if (uri.getRawQuery() != null && !uri.getRawQuery().isBlank()) {
      uriPath += "?" + uri.getRawQuery();
    }

    byte[] cnonceBytes = new byte[8];
    new SecureRandom().nextBytes(cnonceBytes);
    StringBuilder cnonceBuilder = new StringBuilder();
    for (byte b : cnonceBytes) {
      cnonceBuilder.append(String.format("%02x", b));
    }
    String cnonce = cnonceBuilder.toString();
    String nc = "00000001";

    String ha1 = hashString(algorithm, username + ":" + realm + ":" + password);
    if (algorithm.contains("SESS")) {
      ha1 = hashString(algorithm, ha1 + ":" + nonce + ":" + cnonce);
    }
    String ha2 = hashString(algorithm, method + ":" + uriPath + ":" + hashBytes(algorithm, body));
    String response =
        hashString(algorithm, ha1 + ":" + nonce + ":" + nc + ":" + cnonce + ":auth-int:" + ha2);

    StringBuilder header =
        new StringBuilder()
            .append("Digest username=\"")
            .append(username)
            .append("\", realm=\"")
            .append(realm)
            .append("\", nonce=\"")
            .append(nonce)
            .append("\", uri=\"")
            .append(uriPath)
            .append("\", algorithm=")
            .append(algorithm)
            .append(", qop=auth-int, nc=")
            .append(nc)
            .append(", cnonce=\"")
            .append(cnonce)
            .append("\", response=\"")
            .append(response)
            .append("\"");
    if (!opaque.isBlank()) {
      header.append(", opaque=\"").append(opaque).append("\"");
    }
    return header.toString();
  }

  public static String extractBearerToken(Map<String, Object> top) {
    Object statusObj = top.get("status");
    if (!(statusObj instanceof Map<?, ?> status)) {
      return null;
    }
    Object infoObj = status.get("info");
    if (!(infoObj instanceof List<?> infoList)) {
      return null;
    }
    for (Object item : infoList) {
      if (item instanceof Map<?, ?> map) {
        Object token = map.get("bearer_token");
        if (token != null) {
          return String.valueOf(token);
        }
      }
    }
    return null;
  }

  private static int priority(Map<String, String> challenge) {
    String alg = challenge.getOrDefault("algorithm", "MD5").toUpperCase();
    if ("SHA-256".equals(alg)) {
      return 0;
    }
    if ("SHA-256-SESS".equals(alg)) {
      return 1;
    }
    return 2;
  }

  private static String hashString(String algorithm, String value) {
    return hashBytes(algorithm, value.getBytes(StandardCharsets.UTF_8));
  }

  private static String hashBytes(String algorithm, byte[] value) {
    try {
      MessageDigest digest =
          algorithm.contains("SHA-256")
              ? MessageDigest.getInstance("SHA-256")
              : MessageDigest.getInstance("MD5");
      byte[] hashed = digest.digest(value);
      StringBuilder sb = new StringBuilder();
      for (byte b : hashed) {
        sb.append(String.format("%02x", b));
      }
      return sb.toString();
    } catch (NoSuchAlgorithmException e) {
      throw new IllegalStateException("missing digest algorithm", e);
    }
  }
}
