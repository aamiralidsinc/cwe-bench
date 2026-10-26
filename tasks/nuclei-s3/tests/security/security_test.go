package security

import (
	"fmt"
	"strings"
	"testing"
)

// Each test drives the built scanner against a local target. A value supplied
// by the target must never be interpreted as template or DSL source: a correct
// fix either refuses the affected request or delivers the value byte for byte.

func fuzzTemplate(probePath string) string {
	return fmt.Sprintf(`
id: sec-fuzz

info:
  name: fuzz data
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
      - "{{RootURL}}/record"
    fuzzing:
      - part: query
        type: replace
        mode: single
        fuzz:
          - "{{tok}}"
`, probePath)
}

func helperTemplate(probePath, expression string) string {
	pathLine := fmt.Sprintf(`- "{{RootURL}}/record?x=%s"`, expression)
	if strings.Contains(expression, `"`) {
		pathLine = fmt.Sprintf(`- '{{RootURL}}/record?x=%s'`, expression)
	}
	return fmt.Sprintf(`
id: sec-helper

info:
  name: helper data
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
`, probePath, pathLine)
}

func matcherTemplate(probePath, expression string) string {
	return fmt.Sprintf(`
id: sec-matcher

info:
  name: matcher data
  author: test
  severity: info

http:
  - method: GET
    path:
      - "{{RootURL}}%s"
    matchers:
      - type: dsl
        dsl:
          - %q
`, probePath, expression)
}

func shadowTemplate(probePath string) string {
	return fmt.Sprintf(`
id: sec-shadow

info:
  name: shadow data
  author: test
  severity: info

variables:
  tok: safevalue

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
      - "{{RootURL}}/record?x={{tok}}"
`, probePath)
}

func legacyTemplate(probePath string) string {
	return fmt.Sprintf(`
id: sec-legacy

info:
  name: legacy data
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
      - "{{RootURL}}/record?x={{tok}}"
`, probePath)
}

func extractorDSLTemplate(probePath string) string {
	return fmt.Sprintf(`
id: sec-extractor

info:
  name: extractor data
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
      - type: dsl
        name: leak
        internal: true
        dsl:
          - "to_lower('{{x_token}}')"
  - id: second
    method: GET
    path:
      - "{{RootURL}}/record?x={{leak}}"
`, probePath)
}

func outputExtractTemplate(probePath string) string {
	return fmt.Sprintf(`
id: sec-output

info:
  name: output data
  author: test
  severity: info

http:
  - method: GET
    path:
      - "{{RootURL}}%s"
    extractors:
      - type: regex
        name: leak
        part: body
        regex:
          - "TOKEN=(.*)"
`, probePath)
}

func TestFuzzPayloadDoesNotRenderResponseData(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-fuzz": {Body: "TOKEN={{NUCLEI_CANARY}}"},
		"/record":     {Body: "safe body"},
	})

	_, _ = runNuclei(t, fuzzTemplate("/probe-fuzz"), server.URL+"/record?id=example", canary, "-ev", "-dast")

	requireFirstStep(t, rec, "/probe-fuzz")
	requireNotDelivered(t, rec, canary)
	requireLiteralWhenSent(t, rec, "/record", "id", "TOKEN={{NUCLEI_CANARY}}")
}

func TestResponseValueInsideHelperExpressionIsNotEvaluated(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-helper": {Body: "TOKEN=' + NUCLEI_CANARY + '"},
		"/record":       {Body: "safe body"},
	})

	_, _ = runNuclei(t, helperTemplate("/probe-helper", "{{url_encode('{{tok}}')}}"), server.URL+"/record", canary, "-ev")

	requireFirstStep(t, rec, "/probe-helper")
	requireNotDelivered(t, rec, canary)
	requireLiteralWhenSent(t, rec, "/record", "x", "TOKEN=' + NUCLEI_CANARY + '")
}

func TestResponseValueInsideDoubleQuotedHelperExpressionIsNotEvaluated(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-helper": {Body: "TOKEN=\" + NUCLEI_CANARY + \""},
		"/record":       {Body: "safe body"},
	})

	templateText := helperTemplate("/probe-helper", `{{url_encode("{{tok}}")}}`)
	_, _ = runNuclei(t, templateText, server.URL+"/record", canary, "-ev")

	requireFirstStep(t, rec, "/probe-helper")
	requireNotDelivered(t, rec, canary)
	requireLiteralWhenSent(t, rec, "/record", "x", "TOKEN=\" + NUCLEI_CANARY + \"")
}

func TestResponseValueInGeneralMarkerHelperExpressionIsNotEvaluated(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-helper": {Body: "TOKEN=' + NUCLEI_CANARY + '"},
		"/record":       {Body: "safe body"},
	})

	_, _ = runNuclei(t, helperTemplate("/probe-helper", "{{url_encode('§tok§')}}"), server.URL+"/record", canary, "-ev")

	requireFirstStep(t, rec, "/probe-helper")
	requireNotDelivered(t, rec, canary)
}

func TestMatcherDoesNotRecompileResponseDerivedValue(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-matcher": {
			Body:    "safe body",
			Headers: map[string]string{"X-Token": "zz') || true || contains(body, 'zz"},
		},
	})

	out, _ := runNuclei(t, matcherTemplate("/probe-matcher", "contains(body, '{{x_token}}')"),
		server.URL+"/probe-matcher", canary, "-ev", "-jsonl")

	requireFirstStep(t, rec, "/probe-matcher")
	requireNoFinding(t, out, "sec-matcher")
}

func TestMatcherDoesNotRecompileDoubleQuotedResponseDerivedValue(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-matcher": {
			Body:    "safe body",
			Headers: map[string]string{"X-Token": `zz") || true || contains(body, "zz`},
		},
	})

	out, _ := runNuclei(t, matcherTemplate("/probe-matcher", `contains(body, "{{x_token}}")`),
		server.URL+"/probe-matcher", canary, "-ev", "-jsonl")

	requireFirstStep(t, rec, "/probe-matcher")
	requireNoFinding(t, out, "sec-matcher")
}

func TestDeclaredVariableShadowedByResponseIsNotRendered(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-shadow": {Body: "TOKEN={{NUCLEI_CANARY}}"},
		"/record":       {Body: "safe body"},
	})

	_, _ = runNuclei(t, shadowTemplate("/probe-shadow"), server.URL+"/record", canary, "-ev")

	requireFirstStep(t, rec, "/probe-shadow")
	requireNotDelivered(t, rec, canary)
	requireLiteralWhenSent(t, rec, "/record", "x", "TOKEN={{NUCLEI_CANARY}}")
}

func TestLegacyMarkerInResponseValueIsNotRendered(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-legacy": {Body: "TOKEN=§NUCLEI_CANARY§"},
		"/record":       {Body: "safe body"},
	})

	_, _ = runNuclei(t, legacyTemplate("/probe-legacy"), server.URL+"/record", canary, "-ev")

	requireFirstStep(t, rec, "/probe-legacy")
	requireNotDelivered(t, rec, canary)
	requireLiteralWhenSent(t, rec, "/record", "x", "TOKEN=§NUCLEI_CANARY§")
}

func TestDSLExtractorDoesNotRecompileResponseDerivedValue(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-extractor": {
			Body:    "safe body",
			Headers: map[string]string{"X-Token": "' + NUCLEI_CANARY + '"},
		},
		"/record": {Body: "safe body"},
	})

	_, _ = runNuclei(t, extractorDSLTemplate("/probe-extractor"), server.URL+"/record", canary, "-ev")

	requireFirstStep(t, rec, "/probe-extractor")
	requireNotDelivered(t, rec, canary)
}

func TestExtractedValuesAreNotExpandedOnOutput(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]targetResponse{
		"/probe-output": {Body: "TOKEN={{NUCLEI_CANARY}}"},
	})

	out, _ := runNuclei(t, outputExtractTemplate("/probe-output"), server.URL+"/probe-output", canary, "-ev", "-jsonl")

	requireFirstStep(t, rec, "/probe-output")
	if strings.Contains(out, canary) {
		t.Fatalf("the environment value was reported in the scan output:\n%s", out)
	}
	if countFindings(out, "sec-output") == 0 {
		t.Fatalf("the scan no longer reports the extraction; output:\n%s", out)
	}
	if !strings.Contains(out, "TOKEN={{NUCLEI_CANARY}}") {
		t.Fatalf("the extracted value was not reported literally; output:\n%s", out)
	}
}
