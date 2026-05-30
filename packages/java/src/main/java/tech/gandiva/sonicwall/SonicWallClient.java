package tech.gandiva.sonicwall;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.http.HttpClient;
import java.security.GeneralSecurityException;
import java.security.cert.X509Certificate;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLParameters;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;
import tech.gandiva.sonicwall.exception.CommitException;
import tech.gandiva.sonicwall.exception.RollbackException;
import tech.gandiva.sonicwall.internal.ApiTransport;
import tech.gandiva.sonicwall.internal.AuthManager;
import tech.gandiva.sonicwall.internal.HostNormalizer;
import tech.gandiva.sonicwall.service.AccessRulesService;
import tech.gandiva.sonicwall.service.AddressObjectsService;
import tech.gandiva.sonicwall.service.DhcpService;
import tech.gandiva.sonicwall.service.InterfacesService;
import tech.gandiva.sonicwall.service.NatPoliciesService;
import tech.gandiva.sonicwall.service.ServiceObjectsService;

/**
 * Java client for the SonicOS REST API.
 *
 * <p>Authentication uses Basic auth + {@code smngsess} cookie (same as TypeScript/Go). For SonicOS
 * 7.x Digest + bearer token devices, use the Python SDK until Java auth parity lands.
 */
public final class SonicWallClient implements AutoCloseable {
  private final AuthManager auth;
  private final ApiTransport transport;

  public final AddressObjectsService addressObjects;
  public final AccessRulesService accessRules;
  public final NatPoliciesService natPolicies;
  public final ServiceObjectsService serviceObjects;
  public final InterfacesService interfaces;
  public final DhcpService dhcp;

  public SonicWallClient(String host, String username, String password) {
    this(host, username, password, ClientOptions.builder().build());
  }

  public SonicWallClient(String host, String username, String password, ClientOptions options) {
    ObjectMapper mapper = new ObjectMapper();
    HttpClient httpClient = options.httpClient() != null ? options.httpClient() : buildHttpClient(options);
    String baseUrl = HostNormalizer.baseUrl(host);
    auth = new AuthManager(baseUrl, username, password, httpClient, mapper);
    transport = new ApiTransport(baseUrl, httpClient, auth, mapper);
    addressObjects = new AddressObjectsService(transport);
    accessRules = new AccessRulesService(transport);
    natPolicies = new NatPoliciesService(transport);
    serviceObjects = new ServiceObjectsService(transport);
    interfaces = new InterfacesService(transport);
    dhcp = new DhcpService(transport);
  }

  /** Authenticates with the appliance if needed. */
  public void connect() {
    auth.ensureAuthenticated();
  }

  /** Logs out and closes the session (best effort). */
  public void disconnect() {
    auth.logout();
  }

  @Override
  public void close() {
    disconnect();
  }

  /** Commits staged pending configuration changes. */
  public void commit() {
    try {
      transport.request("POST", "/config/pending", null);
    } catch (RuntimeException ex) {
      throw new CommitException("commit failed", ex);
    }
  }

  /** Rolls back staged pending configuration changes. */
  public void rollback() {
    try {
      transport.request("DELETE", "/config/pending", null);
    } catch (RuntimeException ex) {
      throw new RollbackException("rollback failed", ex);
    }
  }

  /** Runs {@code action}, commits on success, rolls back on failure. */
  public void transaction(Runnable action) {
    try {
      action.run();
      commit();
    } catch (RuntimeException ex) {
      try {
        rollback();
      } catch (RuntimeException ignored) {
        // preserve original failure
      }
      throw ex;
    }
  }

  private static HttpClient buildHttpClient(ClientOptions options) {
    HttpClient.Builder builder =
        HttpClient.newBuilder().connectTimeout(options.timeout()).followRedirects(HttpClient.Redirect.NORMAL);
    if (options.tlsSkipVerify()) {
      builder.sslContext(trustAllSslContext());
      SSLParameters sslParameters = new SSLParameters();
      sslParameters.setEndpointIdentificationAlgorithm("");
      builder.sslParameters(sslParameters);
    }
    return builder.build();
  }

  private static SSLContext trustAllSslContext() {
    try {
      TrustManager[] trustAll =
          new TrustManager[] {
            new X509TrustManager() {
              @Override
              public void checkClientTrusted(X509Certificate[] chain, String authType) {}

              @Override
              public void checkServerTrusted(X509Certificate[] chain, String authType) {}

              @Override
              public X509Certificate[] getAcceptedIssuers() {
                return new X509Certificate[0];
              }
            }
          };
      SSLContext ctx = SSLContext.getInstance("TLS");
      ctx.init(null, trustAll, new java.security.SecureRandom());
      return ctx;
    } catch (GeneralSecurityException e) {
      throw new IllegalStateException("failed to initialize TLS context", e);
    }
  }
}
