package sonicwall

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strings"
	"sync"
)

// sessionCookieName is the SonicOS session cookie name.
const sessionCookieName = "smngsess"

// reSessionCookie matches the session cookie value in a Set-Cookie header.
var reSessionCookie = regexp.MustCompile(`smngsess=([^;]+)`)

type authManager struct {
	baseURL   string
	username  string
	password  string
	cookie    string
	authed    bool
	mu        sync.Mutex
	httpClient *http.Client
}

func newAuthManager(baseURL, username, password string, httpClient *http.Client) *authManager {
	return &authManager{
		baseURL:    strings.TrimRight(baseURL, "/"),
		username:   username,
		password:   password,
		httpClient: httpClient,
	}
}

// authenticate performs POST /auth and stores the session cookie.
// Must be called with mu held.
func (a *authManager) authenticate(ctx context.Context) error {
	creds := base64.StdEncoding.EncodeToString([]byte(a.username + ":" + a.password))
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, a.baseURL+"/auth", strings.NewReader("{}"))
	if err != nil {
		return &ConnectionError{Cause: err}
	}
	req.Header.Set("Authorization", "Basic "+creds)
	req.Header.Set("Content-Type", "application/json")

	resp, err := a.httpClient.Do(req)
	if err != nil {
		return &ConnectionError{Cause: err}
	}
	defer func() { _ = resp.Body.Close() }()

	if resp.StatusCode == http.StatusUnauthorized {
		body := &SonicOSErrorResponse{}
		_ = json.NewDecoder(resp.Body).Decode(body)
		return &AuthenticationError{HTTPError{
			StatusCode:   401,
			ResponseBody: body,
			SonicWallError: SonicWallError{message: "authentication failed: invalid credentials"},
		}}
	}
	if resp.StatusCode != http.StatusOK {
		body := &SonicOSErrorResponse{}
		_ = json.NewDecoder(resp.Body).Decode(body)
		return newHTTPError(resp.StatusCode, body)
	}

	// Extract smngsess from Set-Cookie
	cookie := ""
	for _, header := range resp.Header["Set-Cookie"] {
		if m := reSessionCookie.FindStringSubmatch(header); m != nil {
			cookie = m[1]
			break
		}
	}
	// Also check the parsed cookies
	if cookie == "" {
		for _, c := range resp.Cookies() {
			if c.Name == sessionCookieName {
				cookie = c.Value
				break
			}
		}
	}
	if cookie == "" {
		return &AuthenticationError{HTTPError{
			StatusCode: 200,
			SonicWallError: SonicWallError{
				message: "authentication succeeded but no smngsess cookie was returned",
			},
		}}
	}

	a.cookie = cookie
	a.authed = true
	return nil
}

// ensureAuthenticated checks if authenticated, authenticating if needed.
func (a *authManager) ensureAuthenticated(ctx context.Context) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.authed && a.cookie != "" {
		return nil
	}
	return a.authenticate(ctx)
}

// reauthenticate forces re-authentication.
func (a *authManager) reauthenticate(ctx context.Context) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.authed = false
	a.cookie = ""
	return a.authenticate(ctx)
}

// logout sends DELETE /auth.
func (a *authManager) logout(ctx context.Context) error {
	a.mu.Lock()
	cookie := a.cookie
	a.authed = false
	a.cookie = ""
	a.mu.Unlock()

	if cookie == "" {
		return nil
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodDelete, a.baseURL+"/auth", nil)
	if err != nil {
		return nil // Best-effort
	}
	req.Header.Set("Cookie", fmt.Sprintf("%s=%s", sessionCookieName, cookie))
	resp, err := a.httpClient.Do(req)
	if err != nil {
		return nil // Best-effort
	}
	defer func() { _ = resp.Body.Close() }()
	_, _ = io.Copy(io.Discard, resp.Body)
	return nil
}

// cookieHeader returns the Cookie header value for the current session.
func (a *authManager) cookieHeader() string {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.cookie == "" {
		return ""
	}
	return fmt.Sprintf("%s=%s", sessionCookieName, a.cookie)
}

// checkResponseForSessionExpiry inspects a response body for SonicOS code 1085.
func checkResponseForSessionExpiry(body *SonicOSErrorResponse) bool {
	if body == nil {
		return false
	}
	for _, info := range body.Status.Info {
		if info.Code == SonicOSCodeSessionExpired {
			return true
		}
	}
	return false
}