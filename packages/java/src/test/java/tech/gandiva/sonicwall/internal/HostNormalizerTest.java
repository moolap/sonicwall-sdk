package tech.gandiva.sonicwall.internal;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class HostNormalizerTest {

  @Test
  void bareIpGetsHttpsAndApiPath() {
    assertEquals("https://192.168.1.1/api/sonicos", HostNormalizer.baseUrl("192.168.1.1"));
  }

  @Test
  void stripsTrailingSlashes() {
    assertEquals("https://192.168.1.1/api/sonicos", HostNormalizer.baseUrl("192.168.1.1/"));
  }

  @Test
  void preservesExplicitHttpScheme() {
    assertEquals("http://127.0.0.1:8080/api/sonicos", HostNormalizer.baseUrl("http://127.0.0.1:8080"));
  }

  @Test
  void stripsPathFromFullUrl() {
    assertEquals("https://192.168.0.1/api/sonicos", HostNormalizer.baseUrl("https://192.168.0.1/extra/path"));
  }

  @Test
  void stripsPathFromBareHost() {
    assertEquals("https://192.168.0.1/api/sonicos", HostNormalizer.baseUrl("192.168.0.1/foo"));
  }
}
