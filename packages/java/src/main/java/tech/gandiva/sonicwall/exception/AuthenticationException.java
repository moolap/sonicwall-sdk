package tech.gandiva.sonicwall.exception;

import tech.gandiva.sonicwall.model.SonicOsResponse;

public class AuthenticationException extends SonicWallHttpException {
  public AuthenticationException(
      String message, int statusCode, int sonicOsCode, SonicOsResponse body) {
    super(message, statusCode, sonicOsCode, body);
  }
}
