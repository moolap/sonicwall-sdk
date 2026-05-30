package tech.gandiva.sonicwall.support;

import static com.github.tomakehurst.wiremock.client.WireMock.aResponse;
import static com.github.tomakehurst.wiremock.client.WireMock.post;
import static com.github.tomakehurst.wiremock.client.WireMock.stubFor;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;

import com.github.tomakehurst.wiremock.junit5.WireMockRuntimeInfo;
import tech.gandiva.sonicwall.SonicWallClient;

/** Shared WireMock stubs and client factory for integration tests. */
public final class SonicWallTestSupport {
  public static final String AUTH_PATH = "/api/sonicos/auth";
  public static final String SESSION_COOKIE = "test-session";

  private SonicWallTestSupport() {}

  public static void stubAuthSuccess() {
    stubFor(
        post(urlEqualTo(AUTH_PATH))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withHeader("Set-Cookie", "smngsess=" + SESSION_COOKIE)
                    .withBody("{\"status\":{\"success\":true,\"info\":[]}}")));
  }

  public static String applianceBase(WireMockRuntimeInfo wm) {
    return "http://localhost:" + wm.getHttpPort();
  }

  public static String apiPath(String suffix) {
    return "/api/sonicos" + (suffix.startsWith("/") ? suffix : "/" + suffix);
  }

  public static SonicWallClient connectedClient(WireMockRuntimeInfo wm) {
    stubAuthSuccess();
    SonicWallClient client = new SonicWallClient(applianceBase(wm), "admin", "password");
    client.connect();
    return client;
  }

  public static String okStatus() {
    return "{\"status\":{\"success\":true,\"info\":[]}}";
  }
}
