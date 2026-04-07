// Package sonicwall provides a client for the SonicOS REST API.
//
// # Basic usage
//
//	client, err := sonicwall.NewClient("192.168.1.1", "admin", "password")
//	if err != nil {
//	    log.Fatal(err)
//	}
//	ctx := context.Background()
//	if err := client.Connect(ctx); err != nil {
//	    log.Fatal(err)
//	}
//	defer client.Disconnect(ctx)
//
//	objects, err := client.AddressObjects.List(ctx)
//
// # Transactions
//
// Use Transaction to commit or roll back a set of changes atomically:
//
//	err = client.Transaction(ctx, func(ctx context.Context) error {
//	    _, _, err := client.AddressObjects.Ensure(ctx, &sonicwall.AddressObjectIPv4{
//	        Name: "my-server",
//	        Type: sonicwall.AddressObjectTypeHost,
//	        Host: "10.0.0.100",
//	        Zone: "LAN",
//	    })
//	    return err
//	})
//
// # SSL
//
// SonicWall devices commonly use self-signed certificates. TLS verification
// is disabled by default. Enable it with WithTLSSkipVerify(false).
package sonicwall

import (
	"crypto/tls"
	"net/http"
	"time"
)

// Option is a functional option for configuring a Client.
type Option func(*clientConfig)

type clientConfig struct {
	tlsSkipVerify bool
	timeout       time.Duration
	httpClient    *http.Client
}

func defaultConfig() *clientConfig {
	return &clientConfig{
		tlsSkipVerify: true,
		timeout:       30 * time.Second,
	}
}

// WithTLSSkipVerify sets whether to skip TLS certificate verification.
// Default is true (skip verification) because SonicWall devices commonly
// use self-signed certificates.
func WithTLSSkipVerify(skip bool) Option {
	return func(c *clientConfig) {
		c.tlsSkipVerify = skip
	}
}

// WithTimeout sets the HTTP request timeout. Default is 30 seconds.
func WithTimeout(d time.Duration) Option {
	return func(c *clientConfig) {
		c.timeout = d
	}
}

// WithHTTPClient sets a custom http.Client to use for all requests.
// If set, WithTLSSkipVerify and WithTimeout are ignored.
func WithHTTPClient(hc *http.Client) Option {
	return func(c *clientConfig) {
		c.httpClient = hc
	}
}

// NewClient creates a new SonicWall API client.
//
// The client is not authenticated until Connect is called.
func NewClient(host, username, password string, opts ...Option) (*Client, error) {
	cfg := defaultConfig()
	for _, opt := range opts {
		opt(cfg)
	}

	httpClient := cfg.httpClient
	if httpClient == nil {
		transport := &http.Transport{
			TLSClientConfig: &tls.Config{
				InsecureSkipVerify: cfg.tlsSkipVerify, //nolint:gosec
			},
		}
		httpClient = &http.Client{
			Transport: transport,
			Timeout:   cfg.timeout,
		}
	}

	baseURL := "https://" + host + "/api/sonicos"
	c := &Client{
		baseURL:    baseURL,
		httpClient: httpClient,
		auth:       newAuthManager(baseURL, username, password, httpClient),
	}

	// Initialise service fields
	c.AddressObjects = &AddressObjectsService{client: c}

	return c, nil
}