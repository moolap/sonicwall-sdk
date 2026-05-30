package tech.gandiva.sonicwall.exception;

/** Base exception for all SonicWall SDK errors. */
public class SonicWallException extends RuntimeException {
  public SonicWallException(String message) {
    super(message);
  }

  public SonicWallException(String message, Throwable cause) {
    super(message, cause);
  }
}
