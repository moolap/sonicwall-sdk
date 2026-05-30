package tech.gandiva.sonicwall.internal;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import tech.gandiva.sonicwall.exception.AuthenticationException;
import tech.gandiva.sonicwall.exception.ConnectionException;
import tech.gandiva.sonicwall.exception.ExceptionMapper;
import tech.gandiva.sonicwall.exception.SessionExpiredException;
import tech.gandiva.sonicwall.exception.SonicWallHttpException;
import tech.gandiva.sonicwall.model.SonicOsResponse;

public final class ApiTransport {
  private final String baseUrl;
  private final HttpClient httpClient;
  private final AuthManager auth;
  private final ObjectMapper mapper;

  public ApiTransport(String baseUrl, HttpClient httpClient, AuthManager auth, ObjectMapper mapper) {
    this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
    this.httpClient = httpClient;
    this.auth = auth;
    this.mapper = mapper;
  }

  public byte[] request(String method, String path, Object body) {
    auth.ensureAuthenticated();
    try {
      return doRequest(method, path, body);
    } catch (RuntimeException ex) {
      if (isUnauthorized(ex)) {
        auth.reauthenticate();
        return doRequest(method, path, body);
      }
      throw ex;
    }
  }

  public JsonNode getJson(String path) {
    return readTree(request("GET", path, null));
  }

  JsonNode readTree(byte[] data) {
    try {
      return mapper.readTree(data);
    } catch (IOException e) {
      throw new ConnectionException("failed to parse JSON response", e);
    }
  }

  public <T> T readValue(byte[] data, Class<T> type) {
    try {
      return mapper.readValue(data, type);
    } catch (IOException e) {
      throw new ConnectionException("failed to parse JSON response", e);
    }
  }

  public <T> T readValue(byte[] data, TypeReference<T> type) {
    try {
      return mapper.readValue(data, type);
    } catch (IOException e) {
      throw new ConnectionException("failed to parse JSON response", e);
    }
  }

  byte[] toBytes(Object body) {
    try {
      return mapper.writeValueAsBytes(body);
    } catch (IOException e) {
      throw new ConnectionException("failed to serialize request body", e);
    }
  }

  private byte[] doRequest(String method, String path, Object body) {
    String url = baseUrl + "/" + path.replaceFirst("^/+", "");
    HttpRequest.Builder builder =
        HttpRequest.newBuilder().uri(URI.create(url)).header("Accept", "application/json");
    auth.cookieHeader().ifPresent(cookie -> builder.header("Cookie", cookie));

    if (body != null) {
      builder.header("Content-Type", "application/json");
      builder.method(method, HttpRequest.BodyPublishers.ofByteArray(toBytes(body)));
    } else {
      builder.method(method, HttpRequest.BodyPublishers.noBody());
    }

    HttpResponse<String> resp;
    try {
      resp = httpClient.send(builder.build(), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
    } catch (IOException e) {
      throw new ConnectionException("request failed", e);
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new ConnectionException("request interrupted", e);
    }

    SonicOsResponse parsed = parseBody(resp.body());
    if (ExceptionMapper.isSessionExpired(parsed)) {
      throw new SessionExpiredException("session expired", resp.statusCode(), ExceptionMapper.SONICOS_CODE_SESSION_EXPIRED, parsed);
    }
    if (resp.statusCode() != 200) {
      throw ExceptionMapper.mapHttpError(resp.statusCode(), parsed);
    }
    if (parsed != null && parsed.status != null && !parsed.status.success && parsed.status.info != null && !parsed.status.info.isEmpty()) {
      throw ExceptionMapper.mapHttpError(resp.statusCode(), parsed);
    }
    return resp.body().getBytes(StandardCharsets.UTF_8);
  }

  private SonicOsResponse parseBody(String raw) {
    try {
      return mapper.readValue(raw, SonicOsResponse.class);
    } catch (IOException e) {
      return null;
    }
  }

  private static boolean isUnauthorized(RuntimeException ex) {
    return ex instanceof AuthenticationException || ex instanceof SessionExpiredException;
  }
}
