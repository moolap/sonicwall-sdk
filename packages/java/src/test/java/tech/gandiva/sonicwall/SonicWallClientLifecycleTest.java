package tech.gandiva.sonicwall;

import static com.github.tomakehurst.wiremock.client.WireMock.aResponse;
import static com.github.tomakehurst.wiremock.client.WireMock.delete;
import static com.github.tomakehurst.wiremock.client.WireMock.post;
import static com.github.tomakehurst.wiremock.client.WireMock.stubFor;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static tech.gandiva.sonicwall.support.SonicWallTestSupport.apiPath;
import static tech.gandiva.sonicwall.support.SonicWallTestSupport.okStatus;

import com.github.tomakehurst.wiremock.junit5.WireMockRuntimeInfo;
import com.github.tomakehurst.wiremock.junit5.WireMockTest;
import org.junit.jupiter.api.Test;
import tech.gandiva.sonicwall.exception.CommitException;
import tech.gandiva.sonicwall.exception.RollbackException;
import tech.gandiva.sonicwall.support.SonicWallTestSupport;

@WireMockTest
class SonicWallClientLifecycleTest {

  @Test
  void commitCallsPendingEndpoint(WireMockRuntimeInfo wm) {
    SonicWallClient client = SonicWallTestSupport.connectedClient(wm);
    stubFor(
        post(urlEqualTo(apiPath("/config/pending")))
            .willReturn(aResponse().withStatus(200).withBody(okStatus())));
    client.commit();
  }

  @Test
  void rollbackCallsPendingDelete(WireMockRuntimeInfo wm) {
    SonicWallClient client = SonicWallTestSupport.connectedClient(wm);
    stubFor(
        delete(urlEqualTo(apiPath("/config/pending")))
            .willReturn(aResponse().withStatus(200).withBody(okStatus())));
    client.rollback();
  }

  @Test
  void transactionCommitsOnSuccess(WireMockRuntimeInfo wm) {
    SonicWallClient client = SonicWallTestSupport.connectedClient(wm);
    stubFor(
        post(urlEqualTo(apiPath("/config/pending")))
            .willReturn(aResponse().withStatus(200).withBody(okStatus())));
    client.transaction(() -> {});
  }

  @Test
  void transactionRollsBackOnFailure(WireMockRuntimeInfo wm) {
    SonicWallClient client = SonicWallTestSupport.connectedClient(wm);
    stubFor(
        delete(urlEqualTo(apiPath("/config/pending")))
            .willReturn(aResponse().withStatus(200).withBody(okStatus())));
    assertThrows(
        IllegalStateException.class,
        () ->
            client.transaction(
                () -> {
                  throw new IllegalStateException("boom");
                }));
  }

  @Test
  void commitSurfacesCommitException(WireMockRuntimeInfo wm) {
    SonicWallClient client = SonicWallTestSupport.connectedClient(wm);
    stubFor(
        post(urlEqualTo(apiPath("/config/pending")))
            .willReturn(
                aResponse()
                    .withStatus(500)
                    .withBody(
                        """
                        {"status":{"success":false,"info":[{"code":500,"message":"commit failed"}]}}
                        """)));
    assertThrows(CommitException.class, client::commit);
  }

  @Test
  void rollbackSurfacesRollbackException(WireMockRuntimeInfo wm) {
    SonicWallClient client = SonicWallTestSupport.connectedClient(wm);
    stubFor(
        delete(urlEqualTo(apiPath("/config/pending")))
            .willReturn(
                aResponse()
                    .withStatus(500)
                    .withBody(
                        """
                        {"status":{"success":false,"info":[{"code":500,"message":"rollback failed"}]}}
                        """)));
    assertThrows(RollbackException.class, client::rollback);
  }
}
