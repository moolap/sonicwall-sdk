package tech.gandiva.sonicwall.internal;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.locks.ReentrantLock;
import tech.gandiva.sonicwall.exception.AuthenticationException;
import tech.gandiva.sonicwall.exception.ConnectionException;
import tech.gandiva.sonicwall.model.SonicOsResponse;

/** SonicOS auth: Digest+bearer (7.x) with Basic+cookie fallback. */
public final class AuthManager {
  private static final String SESSION_COOKIE = "smngsess";
  private static final byte[] AUTH_BODY = "{}".getBytes(StandardCharsets.UTF_8);

  private enum AuthMode {
    NONE,
    BEARER,
    COOKIE
  }

  private final String baseUrl;
  private final String username;
  private final String password;
  private final HttpClient httpClient;
  private final ObjectMapper mapper;
  private final ReentrantLock lock = new ReentrantLock();

  private String sessionCookie;
  private String bearerToken;
  private AuthMode authMode = AuthMode.NONE;

  public AuthManager(String baseUrl, String username, String password, HttpClient httpClient, ObjectMapper mapper) {
    this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
    this.username = username;
    this.password = password;
    this.httpClient = httpClient;
    this.mapper = mapper;
  }

  public void ensureAuthenticated() {
    lock.lock();
    try {
      if (isAuthenticatedLocked()) {
        return;
      }
      authenticateLocked();
    } finally {
      lock.unlock();
    }
  }

  public void reauthenticate() {
    lock.lock();
    try {
      clearSessionLocked();
      authenticateLocked();
    } finally {
      lock.unlock();
    }
  }

  public void logout() {
    lock.lock();
    String cookie = sessionCookie;
    String token = bearerToken;
    AuthMode mode = authMode;
    clearSessionLocked();
    lock.unlock();

    if (mode == AuthMode.NONE) {
      return;
    }
    try {
      HttpRequest.Builder builder =
          HttpRequest.newBuilder().uri(URI.create(baseUrl + "/auth")).header("Accept", "application/json");
      if (mode == AuthMode.BEARER && token != null && !token.isBlank()) {
        builder.header("Authorization", "Bearer " + token);
      } else if (cookie != null && !cookie.isBlank()) {
        builder.header("Cookie", SESSION_COOKIE + "=" + cookie);
      }
      httpClient.send(builder.DELETE().build(), HttpResponse.BodyHandlers.discarding());
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
    } catch (IOException ignored) {
      // best effort
    }
  }

  Optional<String> authorizationHeader() {
    lock.lock();
    try {
      if (bearerToken == null || bearerToken.isBlank()) {
        return Optional.empty();
      }
      return Optional.of("Bearer " + bearerToken);
    } finally {
      lock.unlock();
    }
  }

  Optional<String> cookieHeader() {
    lock.lock();
    try {
      if (sessionCookie == null || sessionCookie.isBlank()) {
        return Optional.empty();
      }
      return Optional.of(SESSION_COOKIE + "=" + sessionCookie);
    } finally {
      lock.unlock();
    }
  }

  private boolean isAuthenticatedLocked() {
    return authMode != AuthMode.NONE
        && ((authMode == AuthMode.BEARER && bearerToken != null && !bearerToken.isBlank())
            || (authMode == AuthMode.COOKIE && sessionCookie != null && !sessionCookie.isBlank()));
  }

  private void clearSessionLocked() {
    sessionCookie = null;
    bearerToken = null;
    authMode = AuthMode.NONE;
  }

  private void authenticateLocked() {
    String authUrl = baseUrl + "/auth";
    HttpResponse<String> challengeResp = sendAuthRequest(authUrl, AUTH_BODY, Map.of());

    if (challengeResp.statusCode() == 401) {
      Map<String, String> challenge = DigestAuth.pickAuthIntChallenge(wwwAuthenticate(challengeResp));
      if (challenge != null) {
        String digestHeader =
            DigestAuth.buildDigestAuthHeader(
                "POST", authUrl, AUTH_BODY, username, password, challenge);
        HttpResponse<String> authed =
            sendAuthRequest(authUrl, AUTH_BODY, Map.of("Authorization", digestHeader));
        if (authed.statusCode() == 401) {
          throw authFailure("authentication failed: invalid credentials", 401, authed.body());
        }
        if (authed.statusCode() != 200) {
          throw authFailure("authentication failed", authed.statusCode(), authed.body());
        }
        consumeAuthSuccess(authed);
        return;
      }

      String creds =
          Base64.getEncoder().encodeToString((username + ":" + password).getBytes(StandardCharsets.UTF_8));
      HttpResponse<String> basicResp =
          sendAuthRequest(authUrl, AUTH_BODY, Map.of("Authorization", "Basic " + creds));
      if (basicResp.statusCode() == 401) {
        throw authFailure("authentication failed: invalid credentials", 401, basicResp.body());
      }
      if (basicResp.statusCode() != 200) {
        throw authFailure("authentication failed", basicResp.statusCode(), basicResp.body());
      }
      consumeAuthSuccess(basicResp);
      return;
    }

    if (challengeResp.statusCode() != 200) {
      throw authFailure("authentication failed", challengeResp.statusCode(), challengeResp.body());
    }
    consumeAuthSuccess(challengeResp);
  }

  private void consumeAuthSuccess(HttpResponse<String> response) {
    Map<String, Object> top = readTopMap(response.body());
    String token = DigestAuth.extractBearerToken(top);
    if (token != null && !token.isBlank()) {
      bearerToken = token;
      sessionCookie = null;
      authMode = AuthMode.BEARER;
      return;
    }

    String cookie = extractCookie(response);
    if (cookie != null && !cookie.isBlank()) {
      sessionCookie = cookie;
      bearerToken = null;
      authMode = AuthMode.COOKIE;
      return;
    }

    throw new AuthenticationException(
        "authentication succeeded but no bearer_token or smngsess cookie was returned", 200, 0, null);
  }

  private HttpResponse<String> sendAuthRequest(String authUrl, byte[] body, Map<String, String> extraHeaders) {
    HttpRequest.Builder builder =
        HttpRequest.newBuilder()
            .uri(URI.create(authUrl))
            .header("Content-Type", "application/json")
            .header("Accept", "application/json")
            .timeout(Duration.ofSeconds(30))
            .POST(HttpRequest.BodyPublishers.ofByteArray(body));
    extraHeaders.forEach(builder::header);
    try {
      return httpClient.send(builder.build(), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
    } catch (IOException e) {
      throw new ConnectionException("authentication request failed", e);
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new ConnectionException("authentication interrupted", e);
    }
  }

  private AuthenticationException authFailure(String message, int status, String body) {
    SonicOsResponse parsed = parseBody(body);
    return new AuthenticationException(message, status, 0, parsed);
  }

  private Map<String, Object> readTopMap(String raw) {
    try {
      return mapper.readValue(raw, new TypeReference<Map<String, Object>>() {});
    } catch (IOException e) {
      return Map.of();
    }
  }

  private SonicOsResponse parseBody(String raw) {
    try {
      return mapper.readValue(raw, SonicOsResponse.class);
    } catch (IOException e) {
      return null;
    }
  }

  private static List<String> wwwAuthenticate(HttpResponse<String> response) {
    return new ArrayList<>(response.headers().allValues("WWW-Authenticate"));
  }

  private static String extractCookie(HttpResponse<String> resp) {
    for (String header : resp.headers().allValues("Set-Cookie")) {
      for (String part : header.split(";")) {
        String trimmed = part.trim();
        if (trimmed.startsWith(SESSION_COOKIE + "=")) {
          return trimmed.substring((SESSION_COOKIE + "=").length());
        }
      }
    }
    return null;
  }
}
