package sonicwall

import (
	"bytes"
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

const sessionCookieName = "smngsess"

var reSessionCookie = regexp.MustCompile(`smngsess=([^;]+)`)

type authMode int

const (
	authModeNone authMode = iota
	authModeBearer
	authModeCookie
)

type authManager struct {
	baseURL     string
	username    string
	password    string
	cookie      string
	bearerToken string
	mode        authMode
	authed      bool
	mu          sync.Mutex
	httpClient  *http.Client
}

func newAuthManager(baseURL, username, password string, httpClient *http.Client) *authManager {
	return &authManager{
		baseURL:    strings.TrimRight(baseURL, "/"),
		username:   username,
		password:   password,
		httpClient: httpClient,
	}
}

func (a *authManager) authenticate(ctx context.Context) error {
	authURL := a.baseURL + "/auth"
	body := []byte("{}")

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, authURL, bytes.NewReader(body))
	if err != nil {
		return &ConnectionError{Cause: err}
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := a.httpClient.Do(req)
	if err != nil {
		return &ConnectionError{Cause: err}
	}
	defer func() { _ = resp.Body.Close() }()

	respBody, _ := io.ReadAll(resp.Body)

	if resp.StatusCode == http.StatusUnauthorized {
		challenge := pickAuthIntChallenge(resp.Header.Values("WWW-Authenticate"))
		if challenge != nil {
			return a.authenticateDigest(ctx, authURL, body, challenge)
		}
		return a.authenticateBasicCookie(ctx, authURL, body)
	}

	if resp.StatusCode != http.StatusOK {
		parsed := &SonicOSErrorResponse{}
		_ = json.Unmarshal(respBody, parsed)
		return newHTTPError(resp.StatusCode, parsed)
	}

	return a.consumeAuthSuccess(resp, respBody)
}

func (a *authManager) authenticateDigest(ctx context.Context, authURL string, body []byte, challenge digestChallenge) error {
	authHeader := buildDigestAuthHeader(http.MethodPost, authURL, body, a.username, a.password, challenge)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, authURL, bytes.NewReader(body))
	if err != nil {
		return &ConnectionError{Cause: err}
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("Authorization", authHeader)

	resp, err := a.httpClient.Do(req)
	if err != nil {
		return &ConnectionError{Cause: err}
	}
	defer func() { _ = resp.Body.Close() }()

	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode == http.StatusUnauthorized {
		parsed := &SonicOSErrorResponse{}
		_ = json.Unmarshal(respBody, parsed)
		return &AuthenticationError{HTTPError{
			StatusCode:     401,
			ResponseBody:   parsed,
			SonicWallError: SonicWallError{message: "authentication failed: invalid credentials"},
		}}
	}
	if resp.StatusCode != http.StatusOK {
		parsed := &SonicOSErrorResponse{}
		_ = json.Unmarshal(respBody, parsed)
		return newHTTPError(resp.StatusCode, parsed)
	}
	return a.consumeAuthSuccess(resp, respBody)
}

func (a *authManager) authenticateBasicCookie(ctx context.Context, authURL string, body []byte) error {
	creds := base64.StdEncoding.EncodeToString([]byte(a.username + ":" + a.password))
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, authURL, bytes.NewReader(body))
	if err != nil {
		return &ConnectionError{Cause: err}
	}
	req.Header.Set("Authorization", "Basic "+creds)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := a.httpClient.Do(req)
	if err != nil {
		return &ConnectionError{Cause: err}
	}
	defer func() { _ = resp.Body.Close() }()

	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode == http.StatusUnauthorized {
		parsed := &SonicOSErrorResponse{}
		_ = json.Unmarshal(respBody, parsed)
		return &AuthenticationError{HTTPError{
			StatusCode:     401,
			ResponseBody:   parsed,
			SonicWallError: SonicWallError{message: "authentication failed: invalid credentials"},
		}}
	}
	if resp.StatusCode != http.StatusOK {
		parsed := &SonicOSErrorResponse{}
		_ = json.Unmarshal(respBody, parsed)
		return newHTTPError(resp.StatusCode, parsed)
	}
	return a.consumeAuthSuccess(resp, respBody)
}

func (a *authManager) consumeAuthSuccess(resp *http.Response, respBody []byte) error {
	parsed := &SonicOSErrorResponse{}
	_ = json.Unmarshal(respBody, parsed)

	if token := extractBearerToken(parsed); token != "" {
		a.bearerToken = token
		a.cookie = ""
		a.mode = authModeBearer
		a.authed = true
		return nil
	}

	cookie := ""
	for _, header := range resp.Header["Set-Cookie"] {
		if m := reSessionCookie.FindStringSubmatch(header); m != nil {
			cookie = m[1]
			break
		}
	}
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
				message: "authentication succeeded but no bearer_token or smngsess cookie was returned",
			},
		}}
	}

	a.cookie = cookie
	a.bearerToken = ""
	a.mode = authModeCookie
	a.authed = true
	return nil
}

func (a *authManager) ensureAuthenticated(ctx context.Context) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.authed && (a.bearerToken != "" || a.cookie != "") {
		return nil
	}
	return a.authenticate(ctx)
}

func (a *authManager) reauthenticate(ctx context.Context) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.authed = false
	a.cookie = ""
	a.bearerToken = ""
	a.mode = authModeNone
	return a.authenticate(ctx)
}

func (a *authManager) logout(ctx context.Context) error {
	a.mu.Lock()
	cookie := a.cookie
	token := a.bearerToken
	mode := a.mode
	a.authed = false
	a.cookie = ""
	a.bearerToken = ""
	a.mode = authModeNone
	a.mu.Unlock()

	if mode == authModeNone {
		return nil
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodDelete, a.baseURL+"/auth", nil)
	if err != nil {
		return nil
	}
	req.Header.Set("Accept", "application/json")
	if mode == authModeBearer && token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	} else if cookie != "" {
		req.Header.Set("Cookie", fmt.Sprintf("%s=%s", sessionCookieName, cookie))
	}
	resp, err := a.httpClient.Do(req)
	if err != nil {
		return nil
	}
	defer func() { _ = resp.Body.Close() }()
	_, _ = io.Copy(io.Discard, resp.Body)
	return nil
}

func (a *authManager) cookieHeader() string {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.cookie == "" {
		return ""
	}
	return fmt.Sprintf("%s=%s", sessionCookieName, a.cookie)
}

func (a *authManager) authorizationHeader() string {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.bearerToken == "" {
		return ""
	}
	return "Bearer " + a.bearerToken
}

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
