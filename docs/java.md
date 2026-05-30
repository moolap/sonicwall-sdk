# Java SDK

Maven coordinates: **`tech.gandiva:sonicwall-sdk`** (see `packages/java/pom.xml`).

## Requirements

- Java **17+**
- Maven **3.9+**

## Installation

Add to `pom.xml`:

```xml
<dependency>
  <groupId>tech.gandiva</groupId>
  <artifactId>sonicwall-sdk</artifactId>
  <version>0.1.0</version>
</dependency>
```

For local development, install from the repo:

```bash
cd packages/java && mvn install
```

## Client lifecycle

```java
SonicWallClient client = new SonicWallClient(host, username, password);
client.connect();
try {
  // ...
} finally {
  client.disconnect();
}
```

Or use try-with-resources (`AutoCloseable`).

## TLS

Self-signed appliance certificates are accepted by default (`tlsSkipVerify` defaults to `true`). For strict verification:

```java
import tech.gandiva.sonicwall.ClientOptions;

SonicWallClient client =
    new SonicWallClient(
        host,
        user,
        pass,
        ClientOptions.builder().tlsSkipVerify(false).build());
```

## Errors

Typed exceptions mirror other SDKs:

- `NotFoundException`, `ConflictException`
- `AuthenticationException`, `SessionExpiredException`, `AuthorizationException`
- `CommitException`, `RollbackException`, `ConnectionException`

## Parity status

Java matches the **TypeScript/Go** CRUD surface for address objects, access rules, NAT policies, service objects, interfaces, and DHCP. See [language-parity.md](language-parity.md) for the full matrix.

**Python** remains the reference for sync client ergonomics and live-validation scripts.
