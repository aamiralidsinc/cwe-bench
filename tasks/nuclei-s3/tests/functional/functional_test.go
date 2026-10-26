package functional

import (
	"encoding/base64"
	"fmt"
	"net/url"
	"strings"
	"testing"
)

// Each test exercises a behaviour that must keep working: template-authored
// text is rendered, and a value supplied by the target is still used literally.

func linkedTemplate(probePath, secondExpression string) string {
	pathLine := fmt.Sprintf(`- "{{RootURL}}/record?x=%s"`, secondExpression)
	if strings.Contains(secondExpression, `"`) {
		pathLine = fmt.Sprintf(`- '{{RootURL}}/record?x=%s'`, secondExpression)
	}
	return fmt.Sprintf(`
id: fun-linked

info:
  name: linked
  author: test
  severity: info

flow: |
  http(1);
  http(2);

http:
  - id: first
    method: GET
    path:
      - "{{RootURL}}%s"
    extractors:
      - type: regex
        name: tok
        part: body
        internal: true
        regex:
          - "TOKEN=(.*)"
  - id: second
    method: GET
    path:
      %s
    matchers:
      - type: status
        status: [200]
`, probePath, pathLine)
}

func shadowTemplate(probePath, secondExpression string) string {
	return fmt.Sprintf(`
id: fun-shadow

info:
  name: shadow
  author: test
  severity: info

variables:
  tok: placeholder

flow: |
  http(1);
  http(2);

http:
  - id: first
    method: GET
    path:
      - "{{RootURL}}%s"
    extractors:
      - type: regex
        name: tok
        part: body
        internal: true
        regex:
          - "TOKEN=(.*)"
  - id: second
    method: GET
    path:
      - "{{RootURL}}/record?x=%s"
    matchers:
      - type: status
        status: [200]
`, probePath, secondExpression)
}

func TestTemplateAuthoredHelperExpressionRenders(t *testing.T) {
	canary := randomCanary(t)

	t.Run("single quote", func(t *testing.T) {
		server, rec := newTarget(t, map[string]targetResponse{"/record": {Body: "safe body"}})
		target, err := url.Parse(server.URL)
		if err != nil {
			t.Fatalf("could not parse target url: %v", err)
		}

		templateText := fmt.Sprintf(`
id: fun-helper

info:
  name: helper
  author: test
  severity: info

http:
  - method: GET
    path:
      - "{{RootURL}}/record?x={{url_encode('{{Host}}')}}&y={{base64('{{Hostname}}')}}"
    matchers:
      - type: status
        status: [200]
`)
		out, _ := runNuclei(t, templateText, server.URL+"/record", canary)
		requireFirstStep(t, rec, "/record")
		if got := requireSent(t, rec, "/record", "x"); got != target.Hostname() {
			t.Fatalf("url_encode('{{Host}}') delivered %q; want %q; output:\n%s", got, target.Hostname(), out)
		}
		want := base64.StdEncoding.EncodeToString([]byte(target.Host))
		if got := requireSent(t, rec, "/record", "y"); got != want {
			t.Fatalf("base64('{{Hostname}}') delivered %q; want %q; output:\n%s", got, want, out)
		}
	})

	t.Run("double quote", func(t *testing.T) {
		server, rec := newTarget(t, map[string]targetResponse{"/record": {Body: "safe body"}})
		target, err := url.Parse(server.URL)
		if err != nil {
			t.Fatalf("could not parse target url: %v", err)
		}

		templateText := `
id: fun-helper

info:
  name: helper
  author: test
  severity: info

http:
  - method: GET
    path:
      - '{{RootURL}}/record?x={{url_encode("{{Host}}")}}'
    matchers:
      - type: status
        status: [200]
`
		out, _ := runNuclei(t, templateText, server.URL+"/record", canary)
		requireFirstStep(t, rec, "/record")
		if got := requireSent(t, rec, "/record", "x"); got != target.Hostname() {
			t.Fatalf("url_encode(\"{{Host}}\") delivered %q; want %q; output:\n%s", got, target.Hostname(), out)
		}
	})
}

func TestAuthoredEnvironmentPlaceholderResolves(t *testing.T) {
	canary := randomCanary(t)

	cases := []struct {
		name       string
		expression string
	}{
		{name: "braces", expression: "{{NUCLEI_CANARY}}"},
		{name: "general", expression: "§NUCLEI_CANARY§"},
	}
	for _, item := range cases {
		t.Run(item.name, func(t *testing.T) {
			server, rec := newTarget(t, map[string]targetResponse{"/record": {Body: "safe body"}})
			templateText := fmt.Sprintf(`
id: fun-env

info:
  name: env
  author: test
  severity: info

http:
  - method: GET
    path:
      - "{{RootURL}}/record?e=%s"
    matchers:
      - type: status
        status: [200]
`, item.expression)
			out, _ := runNuclei(t, templateText, server.URL+"/record", canary, "-ev")
			requireFirstStep(t, rec, "/record")
			if got := requireSent(t, rec, "/record", "e"); got != canary {
				t.Fatalf("authored environment placeholder was delivered as %q; want %q; output:\n%s", got, canary, out)
			}
		})
	}
}

func TestExtractedValueDeliveredLiterally(t *testing.T) {
	canary := randomCanary(t)
	const value = `TOKEN=a'b"c\d e`
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-bytes": {Body: value},
		"/record":      {Body: "safe body"},
	})

	out, _ := runNuclei(t, linkedTemplate("/probe-bytes", "{{tok}}"), server.URL+"/record", canary)

	requireFirstStep(t, rec, "/probe-bytes")
	if got := requireSent(t, rec, "/record", "x"); got != value {
		t.Fatalf("the target value was delivered as %q; want the literal %q; output:\n%s", got, value, out)
	}
}

func TestRuntimeValueShadowsDeclaredVariable(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-benign": {Body: "TOKEN=abc123"},
		"/record":       {Body: "safe body"},
	})

	out, _ := runNuclei(t, shadowTemplate("/probe-benign", "{{tok}}"), server.URL+"/record", canary)

	requireFirstStep(t, rec, "/probe-benign")
	if got := requireSent(t, rec, "/record", "x"); got != "TOKEN=abc123" {
		t.Fatalf("the supplied value did not shadow the declared variable; delivered %q; output:\n%s", got, out)
	}
}

func TestMatcherMatchesLiteralResponseToken(t *testing.T) {
	cases := []struct {
		name       string
		expression string
	}{
		{name: "single quote", expression: "contains(body, '{{x_token}}')"},
		{name: "double quote", expression: `contains(body, "{{x_token}}")`},
	}
	for _, item := range cases {
		t.Run(item.name, func(t *testing.T) {
			canary := randomCanary(t)
			server, rec := newTarget(t, map[string]targetResponse{
				"/probe-match": {
					Body:    "prefix needle suffix",
					Headers: map[string]string{"X-Token": "needle"},
				},
			})
			templateText := fmt.Sprintf(`
id: fun-matcher

info:
  name: matcher
  author: test
  severity: info

http:
  - method: GET
    path:
      - "{{RootURL}}/probe-match"
    matchers:
      - type: dsl
        dsl:
          - %q
`, item.expression)
			out, _ := runNuclei(t, templateText, server.URL+"/probe-match", canary, "-ev", "-jsonl")
			requireFirstStep(t, rec, "/probe-match")
			if countFindings(out, "fun-matcher") == 0 {
				t.Fatalf("a literal response token no longer satisfies the matcher; output:\n%s", out)
			}
		})
	}
}

func TestExtractorExpressionResolvesAuthoredPlaceholder(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-extract": {Body: "safe body"},
	})

	templateText := `
id: fun-extractor

info:
  name: extractor
  author: test
  severity: info

http:
  - method: GET
    path:
      - "{{RootURL}}/probe-extract"
    extractors:
      - type: dsl
        name: got
        dsl:
          - "to_upper('{{NUCLEI_CANARY}}')"
`
	out, _ := runNuclei(t, templateText, server.URL+"/probe-extract", canary, "-ev", "-jsonl")

	requireFirstStep(t, rec, "/probe-extract")
	if countFindings(out, "fun-extractor") == 0 {
		t.Fatalf("the extractor no longer reports a result; output:\n%s", out)
	}
	if want := strings.ToUpper(canary); !strings.Contains(out, want) {
		t.Fatalf("authored placeholders no longer resolve in an extractor expression; want %q in output:\n%s", want, out)
	}
}

func TestResponseTextWithLiteralMarkersStaysVisible(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-literal": {Body: "prefix {{unknown_var}} suffix"},
	})

	templateText := `
id: fun-literal

info:
  name: literal
  author: test
  severity: info

http:
  - method: GET
    path:
      - "{{RootURL}}/probe-literal"
    matchers:
      - type: word
        words:
          - "prefix {{unknown_var}} suffix"
`
	out, _ := runNuclei(t, templateText, server.URL+"/probe-literal", canary, "-jsonl")

	requireFirstStep(t, rec, "/probe-literal")
	if countFindings(out, "fun-literal") == 0 {
		t.Fatalf("response text is no longer compared literally; output:\n%s", out)
	}
}

func TestFuzzPayloadRendersAuthoredText(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-fuzz": {Body: "TOKEN=abc123"},
		"/record":     {Body: "safe body"},
	})

	templateText := `
id: fun-fuzz

info:
  name: fuzz
  author: test
  severity: info

flow: |
  http(1);
  http(2);

http:
  - id: first
    method: GET
    path:
      - "{{RootURL}}/probe-fuzz"
    extractors:
      - type: regex
        name: tok
        part: body
        internal: true
        regex:
          - "TOKEN=(.*)"
  - id: second
    method: GET
    path:
      - "{{RootURL}}/record"
    fuzzing:
      - part: query
        type: replace
        mode: single
        fuzz:
          - "pre-{{tok}}-post"
`
	out, _ := runNuclei(t, templateText, server.URL+"/record?id=example", canary, "-ev", "-dast")

	requireFirstStep(t, rec, "/probe-fuzz")
	if got := requireSent(t, rec, "/record", "id"); got != "pre-TOKEN=abc123-post" {
		t.Fatalf("authored fuzz payload was delivered as %q; want %q; output:\n%s", got, "pre-TOKEN=abc123-post", out)
	}
}

func TestScanMatchesAndExitsCleanly(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{"/probe-ok": {Body: "safe body"}})

	templateText := `
id: fun-basic

info:
  name: basic
  author: test
  severity: info

http:
  - method: GET
    path:
      - "{{RootURL}}/probe-ok"
    matchers:
      - type: word
        words:
          - "safe body"
`
	out, code := runNuclei(t, templateText, server.URL+"/probe-ok", canary, "-jsonl")

	requireFirstStep(t, rec, "/probe-ok")
	if countFindings(out, "fun-basic") == 0 {
		t.Fatalf("a basic scan no longer matches; output:\n%s", out)
	}
	if code != 0 {
		t.Fatalf("scanner exited with %d; output:\n%s", code, out)
	}
}
