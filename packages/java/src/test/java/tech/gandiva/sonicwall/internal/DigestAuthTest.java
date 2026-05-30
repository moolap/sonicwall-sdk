package tech.gandiva.sonicwall.internal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class DigestAuthTest {
  @Test
  void pickAuthIntChallengePrefersSha256() {
    Map<String, String> picked =
        DigestAuth.pickAuthIntChallenge(
            List.of(
                "Digest realm=\"x\", nonce=\"1\", algorithm=MD5, qop=\"auth-int\"",
                "Digest realm=\"x\", nonce=\"2\", algorithm=SHA-256, qop=\"auth-int\""));
    assertNotNull(picked);
    assertEquals("SHA-256", picked.get("algorithm"));
  }

  @Test
  void extractBearerTokenFromStatusInfo() {
    Map<String, Object> top =
        Map.of("status", Map.of("info", List.of(Map.of("bearer_token", "jwt-token"))));
    assertEquals("jwt-token", DigestAuth.extractBearerToken(top));
  }
}
