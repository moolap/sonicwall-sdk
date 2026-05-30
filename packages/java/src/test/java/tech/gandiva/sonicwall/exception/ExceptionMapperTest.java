package tech.gandiva.sonicwall.exception;

import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import tech.gandiva.sonicwall.model.SonicOsResponse;

class ExceptionMapperTest {

  @Test
  void mapsSonicOsNotFoundCode() {
    RuntimeException ex =
        ExceptionMapper.mapHttpError(200, body(ExceptionMapper.SONICOS_CODE_NOT_FOUND, "missing"));
    assertInstanceOf(NotFoundException.class, ex);
    assertTrue(ex.getMessage().contains("missing"));
  }

  @Test
  void mapsSonicOsConflictCode() {
    RuntimeException ex =
        ExceptionMapper.mapHttpError(200, body(ExceptionMapper.SONICOS_CODE_ALREADY_EXISTS, "exists"));
    assertInstanceOf(ConflictException.class, ex);
  }

  @Test
  void mapsSessionExpiredCode() {
    RuntimeException ex =
        ExceptionMapper.mapHttpError(
            200, body(ExceptionMapper.SONICOS_CODE_SESSION_EXPIRED, "session expired"));
    assertInstanceOf(SessionExpiredException.class, ex);
  }

  @Test
  void mapsHttp401ToAuthentication() {
    RuntimeException ex = ExceptionMapper.mapHttpError(401, null);
    assertInstanceOf(AuthenticationException.class, ex);
  }

  @Test
  void mapsHttp403ToAuthorization() {
    RuntimeException ex = ExceptionMapper.mapHttpError(403, null);
    assertInstanceOf(AuthorizationException.class, ex);
  }

  @Test
  void isSessionExpiredDetectsInfoCode() {
    assertTrue(ExceptionMapper.isSessionExpired(body(ExceptionMapper.SONICOS_CODE_SESSION_EXPIRED, "x")));
  }

  private static SonicOsResponse body(int code, String message) {
    SonicOsResponse resp = new SonicOsResponse();
    resp.status = new SonicOsResponse.Status();
    resp.status.success = false;
    SonicOsResponse.Info info = new SonicOsResponse.Info();
    info.code = code;
    info.message = message;
    resp.status.info = java.util.List.of(info);
    return resp;
  }
}
