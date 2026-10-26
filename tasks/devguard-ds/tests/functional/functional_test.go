package functional

import (
	"testing"

	"github.com/l3montree-dev/devguard/hidden_harness"
	"github.com/stretchr/testify/mock"
)

func readOnlyMember() hidden_harness.Options {
	return hidden_harness.Options{AC: hidden_harness.AC{OrgMember: true, OrgRead: true, ProjRead: true, AssetRead: true}}
}

func writerMember() hidden_harness.Options {
	return hidden_harness.Options{AC: hidden_harness.AC{OrgMember: true, OrgRead: true, ProjRead: true, AssetRead: true, ProjWrite: true, AssetWrite: true}}
}

func publicVisitor() hidden_harness.Options {
	return hidden_harness.Options{AC: hidden_harness.AC{}, PublicOrg: true, PublicProject: true, PublicAsset: true}
}

// notRefused fails when the authorization layer refused a request that a member must be able to make.
func notRefused(t *testing.T, what string, code int) {
	t.Helper()
	if code == 403 || code == 404 {
		t.Fatalf("%s was refused (%d) for a member who may read the resource", what, code)
	}
}

func TestFunc_ReadOnlyMemberCanTriageFindings(t *testing.T) {
	env := hidden_harness.New(t, readOnlyMember())
	base := hidden_harness.Base()
	id := hidden_harness.UUID
	cases := []struct {
		name, method, path, body string
	}{
		{"dependency sync", "POST", base + "/dependency-vulns/sync/", `{"vulnsReq":[]}`},
		{"dependency batch", "POST", base + "/dependency-vulns/batch/", `{"vulnIds":["` + id + `"],"status":"accepted"}`},
		{"dependency event", "POST", base + "/dependency-vulns/" + id + "/", `{"status":"accepted"}`},
		{"dependency mitigate", "POST", base + "/dependency-vulns/" + id + "/mitigate/", `{"comment":"x"}`},
		{"first-party event", "POST", base + "/first-party-vulns/" + id + "/", `{"status":"accepted"}`},
		{"first-party mitigate", "POST", base + "/first-party-vulns/" + id + "/mitigate/", `{"justification":"x"}`},
	}
	for _, c := range cases {
		c := c
		t.Run(c.name, func(t *testing.T) {
			notRefused(t, c.name, env.Status(c.method, c.path, c.body))
		})
	}
}

func TestFunc_ReadOnlyMemberCanDecideLicenceRisks(t *testing.T) {
	env := hidden_harness.New(t, readOnlyMember())
	base := hidden_harness.Base()
	id := hidden_harness.UUID
	cases := []struct {
		name, method, path, body string
	}{
		{"license risk create", "POST", base + "/license-risks/", `{"componentPurl":"pkg:npm/x@1.0.0","finalLicenseDecision":"MIT"}`},
		{"license risk event", "POST", base + "/license-risks/" + id + "/", `{"status":"accepted"}`},
		{"license risk mitigate", "POST", base + "/license-risks/" + id + "/mitigate/", `{"comment":"x"}`},
		{"license risk decision", "POST", base + "/license-risks/" + id + "/final-license-decision/", `{"license":"MIT"}`},
		{"license refresh", "POST", base + "/components/licenses/refresh/", ""},
	}
	for _, c := range cases {
		c := c
		t.Run(c.name, func(t *testing.T) {
			notRefused(t, c.name, env.Status(c.method, c.path, c.body))
		})
	}
}

func TestFunc_ReadOnlyMemberCanManageVEXRules(t *testing.T) {
	env := hidden_harness.New(t, readOnlyMember())
	base := hidden_harness.Base()
	cases := []struct {
		name, method, path, body string
	}{
		{"create", "POST", base + "/vex-rules/", `{"cveId":"CVE-2024-0001","pathPattern":["pkg:npm/x"]}`},
		{"update", "PUT", base + "/vex-rules/rule-1/", `{"cveId":"CVE-2024-0001"}`},
		{"reapply", "POST", base + "/vex-rules/rule-1/reapply/", ""},
		{"delete", "DELETE", base + "/vex-rules/rule-1/", ""},
	}
	for _, c := range cases {
		c := c
		t.Run(c.name, func(t *testing.T) {
			notRefused(t, "vex rule "+c.name, env.Status(c.method, c.path, c.body))
		})
	}
}

// A member with write access on the asset keeps being able to change its artifacts.
func TestFunc_WriterCanChangeArtifacts(t *testing.T) {
	env := hidden_harness.New(t, writerMember())
	base := hidden_harness.Base()
	notRefused(t, "artifact delete", env.Status("DELETE", base+"/artifacts/art/", ""))
	notRefused(t, "artifact update", env.Status("PUT", base+"/artifacts/art/", `{"artifactName":"art"}`))
	notRefused(t, "artifact create", env.Status("POST", base+"/artifacts/", `{"artifactName":"art"}`))
}

// Public read access keeps working for visitors who are not members.
func TestFunc_PublicReadStillWorks(t *testing.T) {
	env := hidden_harness.New(t, publicVisitor())
	code := env.Status("GET", hidden_harness.Base()+"/", "")
	if code < 200 || code >= 300 {
		t.Fatalf("public read of an asset version returned %d; public read must keep working", code)
	}
}

// Members keep the maintenance actions that sit on the organization and project routes.
func TestFunc_MemberCanUsePolicyMaintenanceActions(t *testing.T) {
	env := hidden_harness.New(t, hidden_harness.Options{
		AC: hidden_harness.AC{OrgMember: true, OrgRead: true, OrgWrite: true, ProjRead: true, ProjWrite: true, AssetRead: true},
	})
	id := hidden_harness.UUID
	notRefused(t, "organization policy reapply", env.Status("POST", hidden_harness.OrgBase()+"/policies/"+id+"/reapply/", `{"name":"x"}`))
	notRefused(t, "project policy enable", env.Status("POST", hidden_harness.ProjectBase()+"/policies/"+id+"/enable/", `{}`))
}

// A member may still bind an installation to the organization.
func TestFunc_MemberCanFinishInstallation(t *testing.T) {
	env := hidden_harness.New(t, hidden_harness.Options{
		AC: hidden_harness.AC{OrgMember: true, OrgRead: true, OrgWrite: true},
	})
	rec := env.Do("GET", hidden_harness.OrgBase()+"/integrations/finish-installation/?installationId=7", "")
	if rec.Code < 200 || rec.Code >= 300 {
		t.Fatalf("the installation callback returned %d for a member; it must keep working", rec.Code)
	}
	env.Installs.AssertCalled(t, "Save", mock.Anything, mock.Anything, mock.Anything)
}
