package tech.gandiva.sonicwall.exception;

import tech.gandiva.sonicwall.model.SonicOsResponse;

/** HTTP-level SonicOS API error. */
public class SonicWallHttpException extends SonicWallException {
  private final int statusCode;
  private final int sonicOsCode;
  private final SonicOsResponse responseBody;

  public SonicWallHttpException(
      String message, int statusCode, int sonicOsCode, SonicOsResponse responseBody) {
    super(message);
    this.statusCode = statusCode;
    this.sonicOsCode = sonicOsCode;
    this.responseBody = responseBody;
  }

  public int statusCode() {
    return statusCode;
  }

  public int sonicOsCode() {
    return sonicOsCode;
  }

  public SonicOsResponse responseBody() {
    return responseBody;
  }
}
