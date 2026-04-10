package sonicwall

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

// Client is the SonicWall API client.
type Client struct {
	baseURL    string
	httpClient *http.Client
	auth       *authManager

	// Services
	AddressObjects  *AddressObjectsService
	AccessRules     *AccessRulesService
	NatPolicies     *NatPoliciesService
	ServiceObjects  *ServiceObjectsService
	Interfaces      *InterfacesService
	Dhcp            *DhcpService
}

// Connect authenticates with the SonicWall device.
func (c *Client) Connect(ctx context.Context) error {
	return c.auth.ensureAuthenticated(ctx)
}

// Disconnect logs out and closes the session.
func (c *Client) Disconnect(ctx context.Context) error {
	return c.auth.logout(ctx)
}

// request performs an authenticated HTTP request against the SonicOS API.
// It handles automatic re-authentication on 401 with a single retry.
func (c *Client) request(ctx context.Context, method, path string, body interface{}) ([]byte, error) {
	if err := c.auth.ensureAuthenticated(ctx); err != nil {
		return nil, err
	}

	data, err := c.doRequest(ctx, method, path, body)
	if err != nil {
		// On auth error, re-authenticate once and retry
		if IsUnauthorized(err) || IsSessionExpired(err) {
			if reauthErr := c.auth.reauthenticate(ctx); reauthErr != nil {
				return nil, reauthErr
			}
			data, err = c.doRequest(ctx, method, path, body)
			if err != nil {
				return nil, err
			}
			return data, nil
		}
		return nil, err
	}
	return data, nil
}

func (c *Client) doRequest(ctx context.Context, method, path string, bodyData interface{}) ([]byte, error) {
	url := c.baseURL + "/" + strings.TrimLeft(path, "/")

	var bodyReader io.Reader
	if bodyData != nil {
		b, err := json.Marshal(bodyData)
		if err != nil {
			return nil, fmt.Errorf("marshal request body: %w", err)
		}
		bodyReader = bytes.NewReader(b)
	}

	req, err := http.NewRequestWithContext(ctx, method, url, bodyReader)
	if err != nil {
		return nil, &ConnectionError{Cause: err}
	}

	req.Header.Set("Accept", "application/json")
	if bodyData != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	if cookie := c.auth.cookieHeader(); cookie != "" {
		req.Header.Set("Cookie", cookie)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, &ConnectionError{Cause: err}
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response body: %w", err)
	}

	// Parse into base response to check status
	var baseResp SonicOSErrorResponse
	_ = json.Unmarshal(respBody, &baseResp)

	// Check for session expiry even on 200
	if checkResponseForSessionExpiry(&baseResp) {
		return nil, &SessionExpiredError{}
	}

	if resp.StatusCode != http.StatusOK {
		return nil, newHTTPError(resp.StatusCode, &baseResp)
	}

	// Check SonicOS-level success flag
	if !baseResp.Status.Success && len(baseResp.Status.Info) > 0 {
		return nil, newHTTPError(resp.StatusCode, &baseResp)
	}

	return respBody, nil
}

// get performs a GET request and unmarshals the response into out.
func (c *Client) get(ctx context.Context, path string, out interface{}) error {
	data, err := c.request(ctx, http.MethodGet, path, nil)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, out)
}

// post performs a POST request and unmarshals the response into out.
func (c *Client) post(ctx context.Context, path string, body, out interface{}) error {
	data, err := c.request(ctx, http.MethodPost, path, body)
	if err != nil {
		return err
	}
	if out != nil {
		return json.Unmarshal(data, out)
	}
	return nil
}

// put performs a PUT request and unmarshals the response into out.
func (c *Client) put(ctx context.Context, path string, body, out interface{}) error {
	data, err := c.request(ctx, http.MethodPut, path, body)
	if err != nil {
		return err
	}
	if out != nil {
		return json.Unmarshal(data, out)
	}
	return nil
}

// del performs a DELETE request.
func (c *Client) del(ctx context.Context, path string) error {
	_, err := c.request(ctx, http.MethodDelete, path, nil)
	return err
}