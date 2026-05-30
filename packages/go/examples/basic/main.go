// Package main demonstrates basic usage of the SonicWall Go SDK.
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	sonicwall "github.com/moolap/sonicwall-sdk/go"
	"github.com/moolap/sonicwall-sdk/go/models"
)

func main() {
	host := envOrDefault("SONICWALL_HOST", "192.168.1.1")
	user := envOrDefault("SONICWALL_USER", "admin")
	pass := envOrDefault("SONICWALL_PASS", "password")

	// Create client — TLS verification disabled by default for self-signed certs
	client, err := sonicwall.NewClient(host, user, pass,
		sonicwall.WithTLSSkipVerify(true),
	)
	if err != nil {
		log.Fatalf("Failed to create client: %v", err)
	}

	ctx := context.Background()

	// Connect (authenticate)
	fmt.Printf("Connecting to SonicWall at %s...\n", host)
	if err := client.Connect(ctx); err != nil {
		log.Fatalf("Authentication failed: %v", err)
	}
	defer func() {
		fmt.Println("Disconnecting...")
		if err := client.Disconnect(ctx); err != nil {
			log.Printf("Logout error (ignored): %v", err)
		}
	}()

	fmt.Println("Authenticated successfully.")

	// List address objects
	objects, err := client.AddressObjects.List(ctx)
	if err != nil {
		log.Fatalf("Failed to list address objects: %v", err)
	}
	fmt.Printf("\nAddress Objects (%d total):\n", len(objects))
	for _, obj := range objects {
		switch obj.Type {
		case models.AddressObjectTypeHost:
			fmt.Printf("  [host]    %-30s  zone=%-10s  ip=%s\n", obj.Name, obj.Zone, obj.Host)
		case models.AddressObjectTypeNetwork:
			fmt.Printf("  [network] %-30s  zone=%-10s  net=%s\n", obj.Name, obj.Zone, obj.Network)
		case models.AddressObjectTypeRange:
			fmt.Printf("  [range]   %-30s  zone=%-10s  %s – %s\n", obj.Name, obj.Zone, obj.RangeStart, obj.RangeEnd)
		case models.AddressObjectTypeFQDN:
			fmt.Printf("  [fqdn]    %-30s  zone=%-10s  domain=%s\n", obj.Name, obj.Zone, obj.FQDN)
		}
	}

	// Create an address object inside a transaction
	fmt.Println("\nCreating address object 'sdk-example-host' in a transaction...")
	err = client.Transaction(ctx, func(ctx context.Context) error {
		newObj := &models.AddressObjectIPv4{
			Name: "sdk-example-host",
			Type: models.AddressObjectTypeHost,
			Host: "10.99.0.1",
			Zone: "LAN",
		}
		result, created, err := client.AddressObjects.Ensure(ctx, newObj)
		if err != nil {
			return fmt.Errorf("ensure address object: %w", err)
		}

		if created {
			fmt.Printf("Created: %s (%s)\n", result.Name, result.Host)
		} else {
			fmt.Printf("Updated existing: %s (%s)\n", result.Name, result.Host)
		}
		return nil
	})
	if err != nil {
		log.Fatalf("Transaction failed: %v", err)
	}
	fmt.Println("Transaction committed.")

	// Fetch the newly created object
	obj, err := client.AddressObjects.Get(ctx, "sdk-example-host")
	if err != nil {
		log.Fatalf("Failed to get object: %v", err)
	}
	fmt.Printf("\nFetched: %s -> %s (zone: %s)\n", obj.Name, obj.Host, obj.Zone)

	// Clean up — delete the example object
	fmt.Println("\nCleaning up (deleting 'sdk-example-host')...")
	err = client.Transaction(ctx, func(ctx context.Context) error {
		return client.AddressObjects.Delete(ctx, "sdk-example-host")
	})
	if err != nil {
		if sonicwall.IsNotFound(err) {
			fmt.Println("Object already deleted.")
		} else {
			log.Fatalf("Delete failed: %v", err)
		}
	} else {
		fmt.Println("Deleted and committed.")
	}

	fmt.Println("\nDone.")
}

func envOrDefault(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
