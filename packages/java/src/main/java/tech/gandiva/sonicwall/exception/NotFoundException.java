package tech.gandiva.sonicwall.exception;

public class NotFoundException extends SonicWallHttpException {
  public NotFoundException(
      String message, int statusCode, int sonicOsCode, tech.gandiva.sonicwall.model.SonicOsResponse body) {
    super(message, statusCode, sonicOsCode, body);
  }
}
