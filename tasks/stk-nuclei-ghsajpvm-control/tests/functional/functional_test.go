package functional

import (
	"fmt"
	"net/url"
	"strings"
	"testing"
)

// The functional tests keep the legitimate behaviour of the engine: template
// authored placeholders and helpers, declared variables, response chaining and
// the exact bytes a fuzzing rule sends for the target's own value.

func queryValue(t *testing.T, rec *recorder, path, name string) string {
	t.Helper()
	var found string
	var seen bool
	for _, req := range rec.all() {
		if req.Path != path || req.Query == nil {
			continue
		}
		value, ok := req.Query[name]
		if !ok || len(value) != 1 {
			continue
		}
		found = value[0]
		seen = true
	}
	if !seen {
		t.Fatalf("no request to %s carried query parameter %q", path, name)
	}
	return found
}

func TestAuthoredEnvironmentPlaceholdersResolve(t *testing.T) {
	canary := randomCanary(t)

	t.Run("braces", func(t *testing.T) {
		server, rec := newTarget(t, map[string]string{"/record": "ok"})
		template := `
id: authored-env-braces
info:
  name: authored env braces
  author: test
  severity: info
http:
  - method: GET
    path:
      - "{{RootURL}}/record?x={{NUCLEI_CANARY}}"
`
		out, code := runNuclei(t, template, server.URL+"/record", canary, "-ev")
		if code != 0 {
			t.Fatalf("scanner exited with %d: %s", code, out)
		}
		if got := queryValue(t, rec, "/record", "x"); got != canary {
			t.Fatalf("authored environment reference rendered as %q; want %q", got, canary)
		}
	})

	t.Run("legacy", func(t *testing.T) {
		server, rec := newTarget(t, map[string]string{"/record": "ok"})
		template := `
id: authored-env-legacy
info:
  name: authored env legacy
  author: test
  severity: info
http:
  - method: GET
    path:
      - "{{RootURL}}/record?x=§NUCLEI_CANARY§"
`
		out, code := runNuclei(t, template, server.URL+"/record", canary, "-ev")
		if code != 0 {
			t.Fatalf("scanner exited with %d: %s", code, out)
		}
		if got := queryValue(t, rec, "/record", "x"); got != canary {
			t.Fatalf("authored legacy reference rendered as %q; want %q", got, canary)
		}
	})
}

func fuzzModeTemplate(ruleType string) string {
	return fmt.Sprintf(`
id: fuzz-%s
info:
  name: fuzz %s
  author: test
  severity: info
http:
  - method: GET
    path:
      - "{{RootURL}}/record"
    fuzzing:
      - part: query
        type: %s
        mode: single
        keys: ["id"]
        fuzz:
          - "-X-"
`, ruleType, ruleType, ruleType)
}

func TestFuzzTargetValueIsSentVerbatim(t *testing.T) {
	cases := map[string]string{
		"prefix":  "-X-abc",
		"postfix": "abc-X-",
		"infix":   "a-X-bc",
	}
	for ruleType, want := range cases {
		t.Run(ruleType, func(t *testing.T) {
			server, rec := newTarget(t, map[string]string{"/record": "ok"})
			out, code := runNuclei(t, fuzzModeTemplate(ruleType), server.URL+"/record?id=abc", "", "-dast")
			if code != 0 {
				t.Fatalf("scanner exited with %d: %s", code, out)
			}
			if got := queryValue(t, rec, "/record", "id"); got != want {
				t.Fatalf("%s mode sent %q; want %q", ruleType, got, want)
			}
		})
	}
}

func TestFuzzTargetMarkerValueStaysLiteral(t *testing.T) {
	canary := randomCanary(t)
	server, rec := newTarget(t, map[string]string{"/record": "ok"})

	target := server.URL + "/record?id=" + url.QueryEscape("§NUCLEI_CANARY§")
	out, code := runNuclei(t, fuzzModeTemplate("prefix"), target, canary, "-dast", "-ev")
	if code != 0 {
		t.Fatalf("scanner exited with %d: %s", code, out)
	}
	want := "-X-§NUCLEI_CANARY§"
	if got := queryValue(t, rec, "/record", "id"); got != want {
		t.Fatalf("prefix mode sent %q; the target's own value must stay literal (%q)", got, want)
	}
}

func TestExtractedValueDeliveredLiterally(t *testing.T) {
	server, rec := newTarget(t, map[string]string{
		"/probe-plain": "TOKEN=plain-token-123",
		"/record":      "ok",
	})
	template := `
id: chain-plain
info:
  name: chain plain
  author: test
  severity: info
http:
  - id: first
    method: GET
    path:
      - "{{RootURL}}/probe-plain"
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
`
	out, code := runNuclei(t, template, server.URL+"/record?id=example", "")
	if code != 0 {
		t.Fatalf("scanner exited with %d: %s", code, out)
	}
	if got := queryValue(t, rec, "/record", "x"); got != "TOKEN=plain-token-123" {
		t.Fatalf("extracted value delivered as %q; want it verbatim", got)
	}
}

func TestTemplateDeclaredVariablesResolve(t *testing.T) {
	server, rec := newTarget(t, map[string]string{"/record": "ok"})
	template := `
id: declared-vars
info:
  name: declared vars
  author: test
  severity: info
variables:
  greeting: "hi-{{Hostname}}"
http:
  - method: GET
    path:
      - "{{RootURL}}/record?x={{greeting}}"
`
	out, code := runNuclei(t, template, server.URL+"/record", "")
	if code != 0 {
		t.Fatalf("scanner exited with %d: %s", code, out)
	}
	host := strings.TrimPrefix(server.URL, "http://")
	if got, want := queryValue(t, rec, "/record", "x"), "hi-"+host; got != want {
		t.Fatalf("declared variable rendered as %q; want %q", got, want)
	}
}

func TestTemplateAuthoredHelperExpressionRenders(t *testing.T) {
	server, rec := newTarget(t, map[string]string{"/record": "ok"})
	template := `
id: authored-helper
info:
  name: authored helper
  author: test
  severity: info
http:
  - method: GET
    path:
      - "{{RootURL}}/record?x={{md5(\"abc\")}}"
`
	out, code := runNuclei(t, template, server.URL+"/record", "")
	if code != 0 {
		t.Fatalf("scanner exited with %d: %s", code, out)
	}
	const md5abc = "900150983cd24fb0d6963f7d28e17f72"
	if got := queryValue(t, rec, "/record", "x"); got != md5abc {
		t.Fatalf("authored helper rendered as %q; want %q", got, md5abc)
	}
}

func TestFuzzNestedAuthoredExpressionRenders(t *testing.T) {
	server, rec := newTarget(t, map[string]string{"/record": "ok"})
	template := `
id: fuzz-nested
info:
  name: fuzz nested
  author: test
  severity: info
http:
  - method: GET
    path:
      - "{{RootURL}}/record"
    fuzzing:
      - part: query
        type: replace
        mode: single
        keys: ["id"]
        fuzz:
          - "{{md5('{{value}}')}}"
`
	out, code := runNuclei(t, template, server.URL+"/record?id=abc", "", "-dast")
	if code != 0 {
		t.Fatalf("scanner exited with %d: %s", code, out)
	}
	const md5abc = "900150983cd24fb0d6963f7d28e17f72"
	if got := queryValue(t, rec, "/record", "id"); got != md5abc {
		t.Fatalf("nested authored expression rendered as %q; want %q", got, md5abc)
	}
}

func TestScanMatchesAndExitsCleanly(t *testing.T) {
	server, rec := newTarget(t, map[string]string{"/record": "findme"})
	template := `
id: plain-match
info:
  name: plain match
  author: test
  severity: info
http:
  - method: GET
    path:
      - "{{RootURL}}/record"
    matchers:
      - type: word
        part: body
        words:
          - "findme"
`
	out, code := runNuclei(t, template, server.URL+"/record", "")
	if code != 0 {
		t.Fatalf("scanner exited with %d: %s", code, out)
	}
	if len(rec.all()) == 0 {
		t.Fatalf("target received no request")
	}
	if !strings.Contains(out, "plain-match") {
		t.Fatalf("scan did not report the match: %s", out)
	}
}
