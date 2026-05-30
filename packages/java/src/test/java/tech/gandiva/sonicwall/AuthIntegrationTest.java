package tech.gandiva.sonicwall;

import static com.github.tomakehurst.wiremock.client.WireMock.aResponse;
import static com.github.tomakehurst.wiremock.client.WireMock.post;
import static com.github.tomakehurst.wiremock.client.WireMock.stubFor;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static tech.gandiva.sonicwall.support.SonicWallTestSupport.AUTH_PATH;
import static tech.gandiva.sonicwall.support.SonicWallTestSupport.applianceBase;

import com.github.tomakehurst.wiremock.junit5.WireMockRuntimeInfo;
import com.github.tomakehurst.wiremock.junit5.WireMockTest;
import org.junit.jupiter.api.Test;
import tech.gandiva.sonicwall.exception.AuthenticationException;
import tech.gandiva.sonicwall.support.SonicWallTestSupport;

@WireMockTest
class AuthIntegrationTest {

  @Test
  void connectFailsOnInvalidCredentials(WireMockRuntimeInfo wm) {
    stubFor(
        post(urlEqualTo(AUTH_PATH))
            .willReturn(
                aResponse()
                    .withStatus(401)
                    .withBody(
                        """
                        {"status":{"success":false,"info":[{"code":401,"message":"invalid credentials"}]}}
                        """)));

    SonicWallClient client = new SonicWallClient(applianceBase(wm), "admin", "wrong");
    assertThrows(AuthenticationException.class, client::connect);
  }

  @Test
  void connectFailsWhenSessionCookieMissing(WireMockRuntimeInfo wm) {
    stubFor(
        post(urlEqualTo(AUTH_PATH))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(SonicWallTestSupport.okStatus())));

    SonicWallClient client = new SonicWallClient(applianceBase(wm), "admin", "password");
    assertThrows(AuthenticationException.class, client::connect);
  }

  @Test
  void connectUsesDigestBearerWhenChallengePresent(WireMockRuntimeInfo wm) {
    stubFor(
        post(urlEqualTo(AUTH_PATH))
            .inScenario("digest")
            .whenScenarioStateIs("Started")
            .willReturn(
                aResponse()
                    .withStatus(401)
                    .withHeader(
                        "WWW-Authenticate",
                        "Digest realm=\"sonicwall\", nonce=\"abc123\", algorithm=SHA-256, qop=\"auth-int\"")
                    .withBody(
                        """
                        {"status":{"success":false,"info":[{"code":401,"message":"Unauthorized"}]}}
                        """))
            .willSetStateTo("challenged"));

    stubFor(
        post(urlEqualTo(AUTH_PATH))
            .inScenario("digest")
            .whenScenarioStateIs("challenged")
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {"status":{"success":true,"info":[{"bearer_token":"test-bearer"}]}}
                        """)));

    SonicWallClient client = new SonicWallClient(applianceBase(wm), "admin", "password");
    assertDoesNotThrow(
        () -> {
          client.connect();
          client.disconnect();
        });
  }

  @Test
  void disconnectIsBestEffortAfterConnect(WireMockRuntimeInfo wm) {
    SonicWallClient client = SonicWallTestSupport.connectedClient(wm);
    assertDoesNotThrow(client::disconnect);
  }
}
