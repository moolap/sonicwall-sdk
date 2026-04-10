# Go SDK — Getting Started

## Requirements

- Go 1.22+

## Installation

```bash
go get github.com/gandiva-tech/sonicwall-sdk/go
```

## Authentication behavior

The current Go SDK implementation authenticates with `Authorization: Basic ...`
to `POST /auth`, then sends `Cookie: smngsess=...` on authenticated requests.

On some SonicOS 7.x devices, auth may require Digest `auth-int` and issue a
bearer token instead. If you encounter that behavior, treat this as a known
firmware-compatibility gap in the current Go client.

## Basic usage

```go
package main

import (
    "context"
    "fmt"
    "log"

    sonicwall "github.com/gandiva-tech/sonicwall-sdk/go"
    "github.com/gandiva-tech/sonicwall-sdk/go/models"
)

func main() {
    client, err := sonicwall.NewClient("192.168.1.1", "admin", "password",
        sonicwall.WithTLSSkipVerify(true), // default; self-signed cert support
    )
    if err != nil {
        log.Fatal(err)
    }

    ctx := context.Background()

    if err := client.Connect(ctx); err != nil {
        log.Fatalf("auth failed: %v", err)
    }
    defer client.Disconnect(ctx)

    // List address objects
    objects, err := client.AddressObjects.List(ctx)
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Found %d address objects\n", len(objects))

    // Get by name
    obj, err := client.AddressObjects.Get(ctx, "LAN Subnet")
    if err != nil {
        if sonicwall.IsNotFound(err) {
            fmt.Println("Not found")
        } else {
            log.Fatal(err)
        }
    } else {
        fmt.Println(obj.Name, obj.Network)
    }
}
```

## Creating objects in a transaction

```go
err = client.Transaction(ctx, func(ctx context.Context) error {
    _, _, err := client.AddressObjects.Ensure(ctx, &models.AddressObjectIPv4{
        Name: "my-server",
        Type: models.AddressObjectTypeHost,
        Host: "10.0.0.100",
        Zone: "LAN",
    })
    return err
})
if err != nil {
    log.Fatal(err)
}
// Transaction auto-committed on success, rolled back on error
```

## Error handling

```go
import "github.com/gandiva-tech/sonicwall-sdk/go"

obj, err := client.AddressObjects.Get(ctx, "doesnt-exist")
if err != nil {
    switch {
    case sonicwall.IsNotFound(err):
        fmt.Println("not found")
    case sonicwall.IsConflict(err):
        fmt.Println("already exists")
    case sonicwall.IsUnauthorized(err):
        fmt.Println("auth error")
    case sonicwall.IsSessionExpired(err):
        fmt.Println("session expired (SDK will re-auth on next request)")
    default:
        log.Fatal(err)
    }
}
```

## Options

```go
import (
    "net/http"
    "time"
)

// Custom timeout
client, _ := sonicwall.NewClient(host, user, pass,
    sonicwall.WithTimeout(60 * time.Second),
)

// Enable SSL verification (for devices with valid certs)
client, _ = sonicwall.NewClient(host, user, pass,
    sonicwall.WithTLSSkipVerify(false),
)

// Bring your own http.Client (e.g. with custom transport)
hc := &http.Client{Transport: myTransport}
client, _ = sonicwall.NewClient(host, user, pass,
    sonicwall.WithHTTPClient(hc),
)
```

## Address object types

```go
// Host
obj := &models.AddressObjectIPv4{
    Name: "server",
    Type: models.AddressObjectTypeHost,
    Host: "10.0.0.1",
    Zone: "LAN",
}

// Network (CIDR)
obj = &models.AddressObjectIPv4{
    Name:    "subnet",
    Type:    models.AddressObjectTypeNetwork,
    Network: "10.0.0.0/24",
    Zone:    "LAN",
}

// Range
obj = &models.AddressObjectIPv4{
    Name:       "pool",
    Type:       models.AddressObjectTypeRange,
    RangeStart: "192.168.1.100",
    RangeEnd:   "192.168.1.200",
    Zone:       "LAN",
}

// FQDN
obj = &models.AddressObjectIPv4{
    Name: "example-com",
    Type: models.AddressObjectTypeFQDN,
    FQDN: "example.com",
    Zone: "WAN",
}
```