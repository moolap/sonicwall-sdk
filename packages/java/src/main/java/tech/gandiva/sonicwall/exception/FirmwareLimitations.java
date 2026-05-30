package tech.gandiva.sonicwall.exception;

/** SonicOS firmware/API limitation classification. */
public final class FirmwareLimitations {
  private FirmwareLimitations() {}

  public static String limitationReason(int statusCode, String message) {
    if (message == null) {
      return null;
    }
    String msg = message.toLowerCase();
    if (msg.contains("api not found")) {
      return "api_not_found";
    }
    if (msg.contains("endpoint is incomplete") || (statusCode == 400 && msg.contains("incomplete"))) {
      return "endpoint_incomplete";
    }
    if (msg.contains("command") && msg.contains("not found")) {
      return "command_not_found";
    }
    if (statusCode == 405 && msg.contains("non config mode")) {
      return "non_config_mode";
    }
    return null;
  }

  public static boolean isFirmwareUnsupportedError(Throwable err) {
    if (err instanceof UnsupportedEndpointException) {
      return true;
    }
    if (err instanceof SonicWallHttpException http) {
      if (limitationReason(http.statusCode(), http.getMessage()) != null) {
        return true;
      }
      if (http.responseBody() != null
          && http.responseBody().status != null
          && http.responseBody().status.info != null
          && !http.responseBody().status.info.isEmpty()) {
        String sonicosMsg = http.responseBody().status.info.get(0).message;
        return limitationReason(http.statusCode(), sonicosMsg) != null;
      }
    }
    if (err instanceof SonicWallException) {
      return limitationReason(0, err.getMessage()) != null;
    }
    return false;
  }
}
