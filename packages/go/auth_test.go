package sonicwall

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestAuthManagerDigestBearer(t *testing.T) {
	t.Parallel()
	callCount := 0
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/auth" {
			http.NotFound(w, r)
			return
		}
		callCount++
		if callCount == 1 {
			w.Header().Set(
				"WWW-Authenticate",
				`Digest realm="sonicwall", nonce="abc123", algorithm=SHA-256, qop="auth-int"`,
			)
			w.WriteHeader(http.StatusUnauthorized)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"status":{"success":true,"info":[{"bearer_token":"jwt-token"}]}}`))
	}))
	defer srv.Close()

	auth := newAuthManager(srv.URL, "admin", "password", srv.Client())
	if err := auth.ensureAuthenticated(context.Background()); err != nil {
		t.Fatalf("ensureAuthenticated: %v", err)
	}
	if got := auth.authorizationHeader(); got != "Bearer jwt-token" {
		t.Fatalf("authorizationHeader = %q", got)
	}
}

func TestPickAuthIntChallenge(t *testing.T) {
	t.Parallel()
	challenge := pickAuthIntChallenge([]string{
		`Digest realm="x", nonce="1", algorithm=MD5, qop="auth-int"`,
		`Digest realm="x", nonce="2", algorithm=SHA-256, qop="auth-int"`,
	})
	if challenge["algorithm"] != "SHA-256" {
		t.Fatalf("expected SHA-256, got %v", challenge["algorithm"])
	}
}
