package tech.gandiva.sonicwall;

import java.time.Duration;
import java.net.http.HttpClient;

/** Configuration for {@link SonicWallClient}. */
public final class ClientOptions {
  private final boolean tlsSkipVerify;
  private final Duration timeout;
  private final HttpClient httpClient;

  private ClientOptions(Builder builder) {
    this.tlsSkipVerify = builder.tlsSkipVerify;
    this.timeout = builder.timeout;
    this.httpClient = builder.httpClient;
  }

  public static Builder builder() {
    return new Builder();
  }

  public boolean tlsSkipVerify() {
    return tlsSkipVerify;
  }

  public Duration timeout() {
    return timeout;
  }

  public HttpClient httpClient() {
    return httpClient;
  }

  public static final class Builder {
    private boolean tlsSkipVerify = true;
    private Duration timeout = Duration.ofSeconds(30);
    private HttpClient httpClient;

    public Builder tlsSkipVerify(boolean skip) {
      this.tlsSkipVerify = skip;
      return this;
    }

    public Builder timeout(Duration timeout) {
      this.timeout = timeout;
      return this;
    }

    public Builder httpClient(HttpClient httpClient) {
      this.httpClient = httpClient;
      return this;
    }

    public ClientOptions build() {
      return new ClientOptions(this);
    }
  }
}
