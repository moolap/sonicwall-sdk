package tech.gandiva.sonicwall.exception;

import tech.gandiva.sonicwall.model.SonicOsResponse;

public class AuthorizationException extends SonicWallHttpException {
  public AuthorizationException(
      String message, int statusCode, int sonicOsCode, SonicOsResponse body) {
    super(message, statusCode, sonicOsCode, body);
  }
}
