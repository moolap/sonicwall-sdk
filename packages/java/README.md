# SonicWall SDK — Java

Java 17+ client for the SonicOS REST API (`tech.gandiva:sonicwall-sdk`).

## Build and test

```bash
cd packages/java
mvn test
mvn verify   # tests + JaCoCo coverage report (target/site/jacoco/)
mvn package
```

Tests use **JUnit 5** and **WireMock** (no live appliance required). Coverage includes unit tests (wire format, errors, host normalization) and integration tests (auth, address objects, other resource lists, commit/rollback/transaction).

## Quick start

```java
import tech.gandiva.sonicwall.SonicWallClient;
import tech.gandiva.sonicwall.model.AddressObject;
import tech.gandiva.sonicwall.model.AddressObjectType;

try (SonicWallClient client = new SonicWallClient("192.168.1.1", "admin", "password")) {
  client.connect();
  var objects = client.addressObjects.list();
  System.out.println("Address objects: " + objects.size());

  client.transaction(
      () ->
          client.addressObjects.ensure(
              new AddressObject()
                  .name("my-server")
                  .zone("LAN")
                  .type(AddressObjectType.HOST)
                  .host("10.0.0.100")));
}
```

## Auth note

Java uses **Basic auth + `smngsess` cookie** (same as TypeScript/Go). For SonicOS **7.x Digest + bearer** appliances, use the **Python** SDK until Java auth parity is implemented.

## API surface

| Service | Operations |
|---------|------------|
| `addressObjects` | list, get, create, update, delete, ensure |
| `accessRules` | list, get, create, update, delete, insertBefore, insertAfter |
| `natPolicies` | list, get, create, update, delete, ensure |
| `serviceObjects` | list, get, create, update, delete, ensure |
| `interfaces` | list, get |
| `dhcp` | listLeases |
| `commit` / `rollback` / `transaction` | pending-config workflow |

See [docs/java.md](../../docs/java.md) and the root [README](../../README.md).
