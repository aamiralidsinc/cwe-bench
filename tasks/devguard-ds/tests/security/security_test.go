package security

import (
	"testing"

	"github.com/l3montree-dev/devguard/hidden_harness"
	"github.com/stretchr/testify/mock"
)

type call struct {
	name, method, path, body string
}

func publicVisitor() hidden_harness.Options {
	return hidden_harness.Options{
		AC:            hidden_harness.AC{},
		PublicOrg:     true,
		PublicProject: true,
		PublicAsset:   true,
	}
}

// Every published and injected write entry point must refuse a public-visibility visitor.
func TestSec_PublicVisitorCannotChangeAssetData(t *testing.T) {
	env := hidden_harness.New(t, publicVisitor())
	base := hidden_harness.Base()
	id := hidden_harness.UUID
	calls := []call{
		{"artifact delete", "DELETE", base + "/artifacts/art/", ""},
		{"artifact update", "PUT", base + "/artifacts/art/", `{"artifactName":"art"}`},
		{"artifact create", "POST", base + "/artifacts/", `{"artifactName":"art"}`},
		{"license refresh", "POST", base + "/components/licenses/refresh/", ""},
		{"dependency sync", "POST", base + "/dependency-vulns/sync/", `{"vulnsReq":[]}`},
		{"dependency batch", "POST", base + "/dependency-vulns/batch/", `{"vulnIds":["` + id + `"],"status":"accepted"}`},
		{"dependency event", "POST", base + "/dependency-vulns/" + id + "/", `{"status":"accepted"}`},
		{"dependency mitigate", "POST", base + "/dependency-vulns/" + id + "/mitigate/", `{"comment":"x"}`},
		{"first-party event", "POST", base + "/first-party-vulns/" + id + "/", `{"status":"accepted"}`},
		{"first-party mitigate", "POST", base + "/first-party-vulns/" + id + "/mitigate/", `{"justification":"x"}`},
		{"license risk create", "POST", base + "/license-risks/", `{"componentPurl":"pkg:npm/x@1.0.0","finalLicenseDecision":"MIT"}`},
		{"license risk event", "POST", base + "/license-risks/" + id + "/", `{"status":"accepted"}`},
		{"license risk mitigate", "POST", base + "/license-risks/" + id + "/mitigate/", `{"comment":"x"}`},
		{"license risk decision", "POST", base + "/license-risks/" + id + "/final-license-decision/", `{"license":"MIT"}`},
		{"vex rule create", "POST", base + "/vex-rules/", `{"cveId":"CVE-2024-0001","pathPattern":["pkg:npm/x"]}`},
		{"vex rule update", "PUT", base + "/vex-rules/rule-1/", `{"cveId":"CVE-2024-0001"}`},
		{"vex rule reapply", "POST", base + "/vex-rules/rule-1/reapply/", ""},
		{"vex rule delete", "DELETE", base + "/vex-rules/rule-1/", ""},
		{"external reference create", "POST", base + "/external-references/", `{"url":"https://example.invalid/x","type":"advisory"}`},
		{"external reference sync", "POST", base + "/external-references/sync/", `{}`},
		{"external reference delete", "DELETE", base + "/external-references/" + id + "/", ""},
		{"organization policy reapply", "POST", hidden_harness.OrgBase() + "/policies/" + id + "/reapply/", `{"name":"x"}`},
		{"project policy enable", "POST", hidden_harness.ProjectBase() + "/policies/" + id + "/enable/", `{}`},
	}
	for _, c := range calls {
		c := c
		t.Run(c.name, func(t *testing.T) {
			code := env.Status(c.method, c.path, c.body)
			if code < 400 || code >= 500 {
				t.Fatalf("%s %s reached its handler for a public-visibility visitor (status %d); the change must be refused with a client error", c.method, c.path, code)
			}
		})
	}
}

// The installation callback is a state-changing entry point too.
func TestSec_PublicVisitorCannotBindInstallation(t *testing.T) {
	env := hidden_harness.New(t, publicVisitor())
	rec := env.Do("GET", hidden_harness.OrgBase()+"/integrations/finish-installation/?installationId=7", "")
	if rec.Code < 400 || rec.Code >= 500 {
		t.Fatalf("the installation callback reached its handler for a public-visibility visitor (status %d); the change must be refused with a client error", rec.Code)
	}
	env.Installs.AssertNotCalled(t, "Save", mock.Anything, mock.Anything, mock.Anything)
}

// Public visibility granted below the organization must not open its data to writes
// either: an organization member who is not a member of the public project.
func TestSec_ProjectVisibilityDoesNotAuthoriseWrites(t *testing.T) {
	env := hidden_harness.New(t, hidden_harness.Options{
		AC:            hidden_harness.AC{OrgMember: true, OrgRead: true},
		PublicOrg:     false,
		PublicProject: true,
		PublicAsset:   true,
	})
	base := hidden_harness.Base()
	id := hidden_harness.UUID
	calls := []call{
		{"dependency event", "POST", base + "/dependency-vulns/" + id + "/", `{"status":"accepted"}`},
		{"artifact delete", "DELETE", base + "/artifacts/art/", ""},
		{"vex rule create", "POST", base + "/vex-rules/", `{"cveId":"CVE-2024-0001","pathPattern":["pkg:npm/x"]}`},
		{"project policy enable", "POST", hidden_harness.ProjectBase() + "/policies/" + id + "/enable/", `{}`},
	}
	for _, c := range calls {
		c := c
		t.Run(c.name, func(t *testing.T) {
			code := env.Status(c.method, c.path, c.body)
			if code < 400 || code >= 500 {
				t.Fatalf("%s %s reached its handler for a non-member of a publicly visible project (status %d); the change must be refused with a client error", c.method, c.path, code)
			}
		})
	}
}

// Public visibility granted on the asset alone must not open its data to writes.
func TestSec_AssetVisibilityDoesNotAuthoriseWrites(t *testing.T) {
	env := hidden_harness.New(t, hidden_harness.Options{
		AC:            hidden_harness.AC{OrgMember: true, OrgRead: true, ProjRead: true},
		PublicOrg:     false,
		PublicProject: false,
		PublicAsset:   true,
	})
	base := hidden_harness.Base()
	id := hidden_harness.UUID
	calls := []call{
		{"dependency event", "POST", base + "/dependency-vulns/" + id + "/", `{"status":"accepted"}`},
		{"artifact delete", "DELETE", base + "/artifacts/art/", ""},
		{"license risk decision", "POST", base + "/license-risks/" + id + "/final-license-decision/", `{"license":"MIT"}`},
	}
	for _, c := range calls {
		c := c
		t.Run(c.name, func(t *testing.T) {
			code := env.Status(c.method, c.path, c.body)
			if code < 400 || code >= 500 {
				t.Fatalf("%s %s reached its handler for a non-member of a publicly visible asset (status %d); the change must be refused with a client error", c.method, c.path, code)
			}
		})
	}
}
