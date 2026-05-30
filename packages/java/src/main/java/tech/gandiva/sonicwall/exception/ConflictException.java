package tech.gandiva.sonicwall.exception;

import tech.gandiva.sonicwall.model.SonicOsResponse;

public class ConflictException extends SonicWallHttpException {
  public ConflictException(String message, int statusCode, int sonicOsCode, SonicOsResponse body) {
    super(message, statusCode, sonicOsCode, body);
  }
}
