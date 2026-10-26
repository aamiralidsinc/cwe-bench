package security

import (
	"fmt"
	"testing"
)

// Control task: only the advisory's own route (response data captured by an
// internal extractor and reused in a fuzzing step) is exercised here.

func fuzzTemplate(payload string) string {
	return fmt.Sprintf(`
id: fuzz-expression

info:
  name: fuzz expression
  author: test
  severity: info

flow: |
  http(1);
  http(2);

http:
  - id: first
    method: GET
    path:
      - "{{RootURL}}/probe-env"
    extractors:
      - type: regex
        name: inj
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
          - '%s'
`, payload)
}

func runFuzz(t *testing.T, payload, literal string, checkLiteral bool) {
	t.Helper()
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]string{
		"/probe-env": "TOKEN={{NUCLEI_CANARY}}",
		"/record":    "ok",
	})

	_, _ = runNuclei(t, fuzzTemplate(payload), server.URL+"/record?id=example", canary, "-ev", "-dast")

	requireFirstStep(t, rec, "/probe-env")
	requireNotDelivered(t, rec, canary)
	if checkLiteral {
		requireLiteralWhenSent(t, rec, "/record", "id", literal)
	}
}

func TestFuzzPayloadDoesNotRenderResponseData(t *testing.T) {
	runFuzz(t, "{{inj}}", "TOKEN={{NUCLEI_CANARY}}", true)
}

func TestFuzzPrefixedPayloadDoesNotRenderResponseData(t *testing.T) {
	runFuzz(t, "PRE-{{inj}}", "", false)
}

func TestFuzzPostfixedPayloadDoesNotRenderResponseData(t *testing.T) {
	runFuzz(t, "{{inj}}-POST", "", false)
}

func TestFuzzHelperWrappedPayloadDoesNotRenderResponseData(t *testing.T) {
	runFuzz(t, `{{md5("x")}}-{{inj}}`, "", false)
}
