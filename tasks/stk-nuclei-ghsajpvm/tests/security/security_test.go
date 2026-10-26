package security

import (
	"fmt"
	"testing"
)

// The target returns response text that names an environment variable. With
// -env-vars the scanner exports that variable. A later step of the template
// reuses the returned text. The value must reach the target as data: either the
// request is refused, or the text is delivered exactly as it arrived.

func chainTemplate(probePath string) string {
	return fmt.Sprintf(`
id: chain-expression

info:
  name: chain expression
  author: test
  severity: info

http:
  - id: first
    method: GET
    path:
      - "{{RootURL}}%s"
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
      - "{{RootURL}}/record?x={{inj}}"
`, probePath)
}

func fuzzTemplate(probePath string) string {
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
      - "{{RootURL}}%s"
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
          - "{{inj}}"
`, probePath)
}

func shadowTemplate(probePath string) string {
	return fmt.Sprintf(`
id: shadow-expression

info:
  name: shadow expression
  author: test
  severity: info

variables:
  inj: safevalue

http:
  - id: first
    method: GET
    path:
      - "{{RootURL}}%s"
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
      - "{{RootURL}}/record?x={{inj}}"
`, probePath)
}

func TestResponseDerivedExpressionIsNotRendered(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]string{
		"/probe-env": "TOKEN={{NUCLEI_CANARY}}",
		"/record":    "ok",
	})

	_, _ = runNuclei(t, chainTemplate("/probe-env"), server.URL+"/record?id=example", canary, "-ev")

	requireFirstStep(t, rec, "/probe-env")
	requireNotDelivered(t, rec, canary)
	requireLiteralWhenSent(t, rec, "/record", "x", "TOKEN={{NUCLEI_CANARY}}")
}

func TestResponseDerivedLegacyMarkerIsNotRendered(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]string{
		"/probe-sect": "TOKEN=§NUCLEI_CANARY§",
		"/record":     "ok",
	})

	_, _ = runNuclei(t, chainTemplate("/probe-sect"), server.URL+"/record?id=example", canary, "-ev")

	requireFirstStep(t, rec, "/probe-sect")
	requireNotDelivered(t, rec, canary)
	requireLiteralWhenSent(t, rec, "/record", "x", "TOKEN=§NUCLEI_CANARY§")
}

func TestFuzzPayloadDoesNotRenderResponseData(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]string{
		"/probe-env": "TOKEN={{NUCLEI_CANARY}}",
		"/record":    "ok",
	})

	_, _ = runNuclei(t, fuzzTemplate("/probe-env"), server.URL+"/record?id=example", canary, "-ev", "-dast")

	requireFirstStep(t, rec, "/probe-env")
	requireNotDelivered(t, rec, canary)
	requireLiteralWhenSent(t, rec, "/record", "id", "TOKEN={{NUCLEI_CANARY}}")
}

func TestFuzzPayloadDoesNotRenderLegacyMarkerData(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]string{
		"/probe-sect": "TOKEN=§NUCLEI_CANARY§",
		"/record":     "ok",
	})

	_, _ = runNuclei(t, fuzzTemplate("/probe-sect"), server.URL+"/record?id=example", canary, "-ev", "-dast")

	requireFirstStep(t, rec, "/probe-sect")
	requireNotDelivered(t, rec, canary)
	requireLiteralWhenSent(t, rec, "/record", "id", "TOKEN=§NUCLEI_CANARY§")
}

func TestShadowedVariableValueIsNotRendered(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]string{
		"/probe-env": "TOKEN={{NUCLEI_CANARY}}",
		"/record":    "ok",
	})

	_, _ = runNuclei(t, shadowTemplate("/probe-env"), server.URL+"/record?id=example", canary, "-ev")

	requireFirstStep(t, rec, "/probe-env")
	requireNotDelivered(t, rec, canary)
	requireLiteralWhenSent(t, rec, "/record", "x", "TOKEN={{NUCLEI_CANARY}}")
}
