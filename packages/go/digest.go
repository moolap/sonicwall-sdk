package sonicwall

import (
	"crypto/md5"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"net/url"
	"regexp"
	"strings"
)

var digestParamRE = regexp.MustCompile(`(\w+)=(?:"([^"]*?)"|([^,\s]+))`)

type digestChallenge map[string]string

func parseDigestChallenge(wwwAuth string) digestChallenge {
	body := strings.TrimSpace(wwwAuth)
	body = regexp.MustCompile(`(?i)^digest\s+`).ReplaceAllString(body, "")
	params := digestChallenge{}
	for _, m := range digestParamRE.FindAllStringSubmatch(body, -1) {
		if len(m) < 3 {
			continue
		}
		val := m[2]
		if val == "" {
			val = m[3]
		}
		params[m[1]] = val
	}
	return params
}

func pickAuthIntChallenge(headers []string) digestChallenge {
	var candidates []digestChallenge
	for _, value := range headers {
		if !strings.HasPrefix(strings.ToLower(value), "digest") {
			continue
		}
		c := parseDigestChallenge(value)
		if strings.Contains(c["qop"], "auth-int") {
			candidates = append(candidates, c)
		}
	}
	if len(candidates) == 0 {
		return nil
	}
	best := candidates[0]
	bestPri := digestPriority(best)
	for _, c := range candidates[1:] {
		if p := digestPriority(c); p < bestPri {
			best = c
			bestPri = p
		}
	}
	return best
}

func digestPriority(c digestChallenge) int {
	alg := strings.ToUpper(c["algorithm"])
	switch {
	case alg == "SHA-256":
		return 0
	case alg == "SHA-256-SESS":
		return 1
	default:
		return 2
	}
}

func buildDigestAuthHeader(method, rawURL string, body []byte, username, password string, challenge digestChallenge) string {
	algorithm := strings.ToUpper(challenge["algorithm"])
	if algorithm == "" {
		algorithm = "MD5"
	}
	realm := challenge["realm"]
	nonce := challenge["nonce"]
	opaque := challenge["opaque"]

	parsed, err := url.Parse(rawURL)
	if err != nil {
		parsed = &url.URL{Path: rawURL}
	}
	uri := parsed.Path
	if parsed.RawQuery != "" {
		uri += "?" + parsed.RawQuery
	}

	cnonceBytes := make([]byte, 8)
	_, _ = rand.Read(cnonceBytes)
	cnonce := hex.EncodeToString(cnonceBytes)
	nc := "00000001"

	hashStr := func(s string) string {
		if strings.Contains(algorithm, "SHA-256") {
			sum := sha256.Sum256([]byte(s))
			return hex.EncodeToString(sum[:])
		}
		sum := md5.Sum([]byte(s))
		return hex.EncodeToString(sum[:])
	}
	hashBytes := func(b []byte) string {
		if strings.Contains(algorithm, "SHA-256") {
			sum := sha256.Sum256(b)
			return hex.EncodeToString(sum[:])
		}
		sum := md5.Sum(b)
		return hex.EncodeToString(sum[:])
	}

	ha1 := hashStr(fmt.Sprintf("%s:%s:%s", username, realm, password))
	if strings.Contains(algorithm, "SESS") {
		ha1 = hashStr(fmt.Sprintf("%s:%s:%s", ha1, nonce, cnonce))
	}
	ha2 := hashStr(fmt.Sprintf("%s:%s:%s", method, uri, hashBytes(body)))
	response := hashStr(fmt.Sprintf("%s:%s:%s:%s:auth-int:%s", ha1, nonce, nc, cnonce, ha2))

	header := fmt.Sprintf(
		`Digest username="%s", realm="%s", nonce="%s", uri="%s", algorithm=%s, qop=auth-int, nc=%s, cnonce="%s", response="%s"`,
		username, realm, nonce, uri, algorithm, nc, cnonce, response,
	)
	if opaque != "" {
		header += fmt.Sprintf(`, opaque="%s"`, opaque)
	}
	return header
}

func extractBearerToken(body *SonicOSErrorResponse) string {
	if body == nil {
		return ""
	}
	for _, info := range body.Status.Info {
		if info.BearerToken != "" {
			return info.BearerToken
		}
	}
	return ""
}
