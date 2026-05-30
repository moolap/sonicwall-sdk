package tech.gandiva.sonicwall.exception;

import tech.gandiva.sonicwall.model.SonicOsResponse;

/** Raised when SonicOS reports an endpoint missing or unusable on this firmware. */
public class UnsupportedEndpointException extends SonicWallHttpException {
  private final String reason;

  public UnsupportedEndpointException(
      String message, int statusCode, int sonicOsCode, SonicOsResponse body, String reason) {
    super(message, statusCode, sonicOsCode, body);
    this.reason = reason;
  }

  public String reason() {
    return reason;
  }
}
