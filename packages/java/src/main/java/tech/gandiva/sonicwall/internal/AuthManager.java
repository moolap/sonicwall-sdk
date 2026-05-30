package tech.gandiva.sonicwall.internal;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Base64;
import java.util.Optional;
import java.util.concurrent.locks.ReentrantLock;
import tech.gandiva.sonicwall.exception.AuthenticationException;
import tech.gandiva.sonicwall.exception.ConnectionException;
import tech.gandiva.sonicwall.exception.ExceptionMapper;
import tech.gandiva.sonicwall.exception.SonicWallHttpException;
import tech.gandiva.sonicwall.model.SonicOsResponse;

/** Cookie-based SonicOS authentication (Basic auth + smngsess), matching TypeScript/Go. */
public final class AuthManager {
  private static final String SESSION_COOKIE = "smngsess";

  private final String baseUrl;
  private final String username;
  private final String password;
  private final HttpClient httpClient;
  private final ObjectMapper mapper;
  private final ReentrantLock lock = new ReentrantLock();

  private String sessionCookie;
  private boolean authed;

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
      if (authed && sessionCookie != null && !sessionCookie.isBlank()) {
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
      authed = false;
      sessionCookie = null;
      authenticateLocked();
    } finally {
      lock.unlock();
    }
  }

  public void logout() {
    lock.lock();
    String cookie;
    try {
      cookie = sessionCookie;
      authed = false;
      sessionCookie = null;
    } finally {
      lock.unlock();
    }
    if (cookie == null || cookie.isBlank()) {
      return;
    }
    try {
      HttpRequest req =
          HttpRequest.newBuilder()
              .uri(URI.create(baseUrl + "/auth"))
              .header("Cookie", SESSION_COOKIE + "=" + cookie)
              .DELETE()
              .build();
      httpClient.send(req, HttpResponse.BodyHandlers.discarding());
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
    } catch (IOException ignored) {
      // best effort
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

  private void authenticateLocked() {
    String creds =
        Base64.getEncoder().encodeToString((username + ":" + password).getBytes(StandardCharsets.UTF_8));
    HttpRequest req =
        HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/auth"))
            .header("Authorization", "Basic " + creds)
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString("{}"))
            .timeout(Duration.ofSeconds(30))
            .build();
    HttpResponse<String> resp;
    try {
      resp = httpClient.send(req, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
    } catch (IOException e) {
      throw new ConnectionException("authentication request failed", e);
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new ConnectionException("authentication interrupted", e);
    }

    if (resp.statusCode() == 401) {
      SonicOsResponse body = parseBody(resp.body());
      throw new AuthenticationException(
          "authentication failed: invalid credentials", 401, 0, body);
    }
    if (resp.statusCode() != 200) {
      SonicOsResponse body = parseBody(resp.body());
      throw ExceptionMapper.mapHttpError(resp.statusCode(), body);
    }

    String cookie = extractCookie(resp);
    if (cookie == null || cookie.isBlank()) {
      throw new AuthenticationException(
          "authentication succeeded but no smngsess cookie was returned", 200, 0, null);
    }
    sessionCookie = cookie;
    authed = true;
  }

  private SonicOsResponse parseBody(String raw) {
    try {
      return mapper.readValue(raw, SonicOsResponse.class);
    } catch (IOException e) {
      return null;
    }
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
