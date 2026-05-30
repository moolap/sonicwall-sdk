package tech.gandiva.sonicwall.exception;

public class RollbackException extends SonicWallException {
  public RollbackException(String message, Throwable cause) {
    super(message, cause);
  }
}
