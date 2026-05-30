package tech.gandiva.sonicwall.exception;

public class ConnectionException extends SonicWallException {
  public ConnectionException(String message, Throwable cause) {
    super(message, cause);
  }
}
