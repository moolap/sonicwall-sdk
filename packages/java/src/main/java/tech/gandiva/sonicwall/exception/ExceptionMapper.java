package tech.gandiva.sonicwall.exception;

import tech.gandiva.sonicwall.model.SonicOsResponse;

public final class ExceptionMapper {
  public static final int SONICOS_CODE_NOT_FOUND = 1030;
  public static final int SONICOS_CODE_ALREADY_EXISTS = 1055;
  public static final int SONICOS_CODE_SESSION_EXPIRED = 1085;

  private ExceptionMapper() {}

  public static RuntimeException mapHttpError(int statusCode, SonicOsResponse body) {
    int sonicOsCode = 0;
    String message = "unexpected status " + statusCode;
    if (body != null && body.status != null && body.status.info != null && !body.status.info.isEmpty()) {
      SonicOsResponse.Info info = body.status.info.get(0);
      sonicOsCode = info.code;
      if (info.message != null && !info.message.isBlank()) {
        message = info.message;
      }
    }

    if (sonicOsCode == SONICOS_CODE_SESSION_EXPIRED) {
      return new SessionExpiredException(message, statusCode, sonicOsCode, body);
    }
    if (sonicOsCode == SONICOS_CODE_NOT_FOUND) {
      return new NotFoundException(message, statusCode, sonicOsCode, body);
    }
    if (sonicOsCode == SONICOS_CODE_ALREADY_EXISTS) {
      return new ConflictException(message, statusCode, sonicOsCode, body);
    }

    return switch (statusCode) {
      case 401 ->
          sonicOsCode == SONICOS_CODE_SESSION_EXPIRED
              ? new SessionExpiredException(message, statusCode, sonicOsCode, body)
              : new AuthenticationException(message, statusCode, sonicOsCode, body);
      case 403 -> new AuthorizationException(message, statusCode, sonicOsCode, body);
      case 404 -> new NotFoundException(message, statusCode, sonicOsCode, body);
      case 409 -> new ConflictException(message, statusCode, sonicOsCode, body);
      default -> mapDefaultHttpError(message, statusCode, sonicOsCode, body);
    };
  }

  private static RuntimeException mapDefaultHttpError(
      String message, int statusCode, int sonicOsCode, SonicOsResponse body) {
    String reason = FirmwareLimitations.limitationReason(statusCode, message);
    if (reason != null) {
      return new UnsupportedEndpointException(message, statusCode, sonicOsCode, body, reason);
    }
    return new SonicWallHttpException(message, statusCode, sonicOsCode, body);
  }

  public static boolean isSessionExpired(SonicOsResponse body) {
    if (body == null || body.status == null || body.status.info == null) {
      return false;
    }
    for (SonicOsResponse.Info info : body.status.info) {
      if (info.code == SONICOS_CODE_SESSION_EXPIRED) {
        return true;
      }
    }
    return false;
  }
}
