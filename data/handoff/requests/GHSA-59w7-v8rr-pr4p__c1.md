<!-- label=GHSA-59w7-v8rr-pr4p call=1 hash=715d7a7809 -->
# SYSTEM
You are a Principal Software Quality Assurance (QA) and Defensive Benchmark Architect on the maintainer side of an evaluation platform. We evaluate whether autonomous AI coding agents can correctly REPAIR real-world vulnerabilities (CVE/GHSA) that have already been fixed upstream in open-source projects.

You are provided with:
1. The historical human fix (the "reference patch")
2. The vulnerable codebase at the pre-patch commit
3. Repository maps, manifests, and test fixtures

Your responsibility is to author:
(1) `instruction.md`: A realistic, fair defect report filed by an enterprise user or security auditor.
(2) `hidden_tests.py`: A black-box pytest regression suite checking security enforcement and functional preservation.
(3) Three validation check-patches (shallow, removal, alternative) to prove the test suite accurately distinguishes good repairs from bad ones.

Operational Principles:
- Purely Defensive: All tests offline, inside an isolated container, using harmless sentinels. Tests only assert that invalid/unauthorized input is safely rejected and legitimate operations execute cleanly.
- Strict Fairness: A task is an exam of model intelligence, NOT a guessing game. Every legitimate use the functional suite tests must be an ordinary use of a FEATURE the report names as "must keep working" (name features, not test values).
- Zero Leakage: The agent must discover the faulty code and every place it lives. Never disclose file names, function names, the hidden place(s), or the scope of the bug ("every provider", "on every route").

# REQUEST
# Defect & Vulnerability Metadata
- OSV ID: GHSA-59w7-v8rr-pr4p
- CVE: CVE-2026-71543
- CWE: CWE-863
- Ecosystem / Package: Go / github.com/openbao/openbao
- Repository: https://github.com/openbao/openbao
- Official Summary: OpenBao's Templated Policies Allow Privilege Escalation via Wildcard Characters

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/builtin/logical/pki/backend_test.go b/builtin/logical/pki/backend_test.go
index 8dafabaa13cb0b52354c3cd9c1804d9c9ef10f11..5ccc19313df2a3e0c3b7df658b590008af1e9127 100644
--- a/builtin/logical/pki/backend_test.go
+++ b/builtin/logical/pki/backend_test.go
@@ -3653,9 +3653,12 @@ func TestBackend_AllowedURISANsTemplate(t *testing.T) {
 
 	// Write test policy for userpass auth method.
 	err := client.Sys().PutPolicy("test", `
-   path "pki/*" {
-     capabilities = ["update"]
-   }`)
+	path "pki/*" {
+		capabilities = ["update", "patch"]
+	}
+	path "identity/entity" {
+		capabilities = ["update"]
+	}`)
 	if err != nil {
 		t.Fatal(err)
 	}
@@ -3681,6 +3684,7 @@ func TestBackend_AllowedURISANsTemplate(t *testing.T) {
 		t.Fatal(err)
 	}
 	userpassToken := secret.Auth.ClientToken
+	entityId := secret.Auth.EntityID
 
 	// Get auth accessor for identity template.
 	auths, err := client.Sys().ListAuth()
@@ -3740,12 +3744,10 @@ func TestBackend_AllowedURISANsTemplate(t *testing.T) {
 	// Issue certificate with non-matching identity template parameter
 	client.SetToken(userpassToken)
 	_, err = client.Logical().Write("pki/issue/test", map[string]interface{}{"uri_sans": "spiffe://domain/unknownuser"})
-	if err == nil {
-		t.Fatal(err)
-	}
+	require.ErrorContains(t, err, "URI Subject Alternative Names were provided via the API which are not valid for this role")
 
 	// Set allowed_uri_sans_template to false.
-	_, err = client.Logical().Write("pki/roles/test", map[string]interface{}{
+	_, err = client.Logical().JSONMergePatch(t.Context(), "pki/roles/test", map[string]interface{}{
 		"allowed_uri_sans_template": false,
 	})
 	if err != nil {
@@ -3754,9 +3756,37 @@ func TestBackend_AllowedURISANsTemplate(t *testing.T) {
 
 	// Issue certificate with userpassToken.
 	_, err = client.Logical().Write("pki/issue/test", map[string]interface{}{"uri_sans": "spiffe://domain/users/userpassname"})
-	if err == nil {
-		t.Fatal("expected error")
-	}
+	require.ErrorContains(t, err, "URI Subject Alternative Names were provided via the API which are not valid for this role")
+
+	// Add wildcard to entity metadata
+	_, err = client.Logical().WriteWithContext(t.Context(), "identity/entity", map[string]any{
+		"id": entityId,
+		"metadata": map[string]any{
+			"sans": "spiffe://domain/users/*",
+		},
+	})
+	require.NoError(t, err)
+
+	// Update Allowed URI SANs to include entity metadata
+	_, err = client.Logical().JSONMergePatch(t.Context(), "pki/roles/test", map[string]any{
+		"allowed_uri_sans":          []string{"{{identity.entity.metadata.sans}}"},
+		"allowed_uri_sans_template": true,
+	})
+	require.NoError(t, err)
+
+	// Expect failure (wildcards are prohibited by default)
+	_, err = client.Logical().WriteWithContext(t.Context(), "pki/issue/test", map[string]any{"uri_sans": "spiffe://domain/users/userpassname"})
+	require.ErrorContains(t, err, "URI Subject Alternative Names were provided via the API which are not valid for this role")
+
+	// Allow Globs
+	_, err = client.Logical().JSONMergePatch(t.Context(), "pki/roles/test", map[string]any{
+		"allow_globs_in_substitutions": true,
+	})
+	require.NoError(t, err)
+
+	// Expect successful issue
+	_, err = client.Logical().WriteWithContext(t.Context(), "pki/issue/test", map[string]any{"uri_sans": "spiffe://domain/users/userpassname"})
+	require.NoError(t, err)
 }
 
 func TestBackend_AllowedDomainsTemplate(t *testing.T) {
@@ -3778,9 +3808,12 @@ func TestBackend_AllowedDomainsTemplate(t *testing.T) {
 
 	// Write test policy for userpass auth method.
 	err := client.Sys().PutPolicy("test", `
-   path "pki/*" {
-     capabilities = ["update"]
-   }`)
+	path "pki/*" {
+		capabilities = ["update", "patch"]
+	}
+	path "identity/entity" {
+		capabilities = ["update"]
+	}`)
 	if err != nil {
 		t.Fatal(err)
 	}
@@ -3840,6 +3873,7 @@ func TestBackend_AllowedDomainsTemplate(t *testing.T) {
 		},
 		"allowed_domains_template": true,
 		"allow_bare_domains":       true,
+		"allow_glob_domains":       true,
 	})
 	if err != nil {
 		t.Fatal(err)
@@ -3853,6 +3887,8 @@ func TestBackend_AllowedDomainsTemplate(t *testing.T) {
 	if err != nil || secret == nil {
 		t.Fatal(err)
 	}
+	entityId := secret.Auth.EntityID
+
 	_, err = client.Logical().Write("pki/issue/test", map[string]interface{}{"common_name": "userpassname"})
 	if err != nil {
 		t.Fatal(err)
@@ -3866,9 +3902,7 @@ func TestBackend_AllowedDomainsTemplate(t *testing.T) {
 
 	// Issue certificate for unknown userpassname.
 	_, err = client.Logical().Write("pki/issue/test", map[string]interface{}{"common_name": "unknownuserpassname"})
-	if err == nil {
-		t.Fatal("expected error")
-	}
+	require.ErrorContains(t, err, "common name unknownuserpassname not allowed by this role")
 
 	// Issue certificate for foo.userpassname.domain.
 	_, err = client.Logical().Write("pki/issue/test", map[string]interface{}{"common_name": "foo.userpassname.example.com"})
@@ -3877,7 +3911,7 @@ func TestBackend_AllowedDomainsTemplate(t *testing.T) {
 	}
 
 	// Set allowed_domains_template to false.
-	_, err = client.Logical().Write("pki/roles/test", map[string]interface{}{
+	_, err = client.Logical().JSONMergePatch(t.Context(), "pki/roles/test", map[string]any{
 		"allowed_domains_template": false,
 	})
 	if err != nil {
@@ -3886,9 +3920,37 @@ func TestBackend_AllowedDomainsTemplate(t *testing.T) {
 
 	// Issue certificate with userpassToken.
 	_, err = client.Logical().Write("pki/issue/test", map[string]interface{}{"common_name": "userpassname"})
-	if err == nil {
-		t.Fatal("expected error")
-	}
+	require.ErrorContains(t, err, "common name userpassname not allowed by this role")
+
+	// Add wildcard to entity metadata
+	_, err = client.Logical().WriteWithContext(t.Context(), "identity/entity", map[string]any{
+		"id": entityId,
+		"metadata": map[string]any{
+			"domains": "*.example.com",
+		},
+	})
+	require.NoError(t, err)
+
+	// Update Allowed Domains to include entity metadata
+	_, err = client.Logical().JSONMergePatch(t.Context(), "pki/roles/test", map[string]any{
+		"allowed_domains":          []string{"{{identity.entity.metadata.domains}}"},
+		"allowed_domains_template": true,
+	})
+	require.NoError(t, err)
+
+	// Expect failure (wildcards are prohibited by default)
+	_, err = client.Logical().WriteWithContext(t.Context(), "pki/issue/test", map[string]any{"common_name": "foo.example.com"})
+	require.ErrorContains(t, err, "common name foo.example.com not allowed by this role")
+
+	// Allow Globs
+	_, err = client.Logical().JSONMergePatch(t.Context(), "pki/roles/test", map[string]any{
+		"allow_globs_in_substitutions": true,
+	})
+	require.NoError(t, err)
+
+	// Expect successful issue
+	_, err = client.Logical().WriteWithContext(t.Context(), "pki/issue/test", map[string]any{"common_name": "foo.example.com"})
+	require.NoError(t, err)
 }
 
 func TestReadWriteDeleteRoles(t *testing.T) {
@@ -3961,6 +4023,7 @@ func TestReadWriteDeleteRoles(t *testing.T) {
 		"policy_identifiers":                 []interface{}{},
 		"require_cn":                         true,
 		"allowed_domains_template":           false,
+		"allow_globs_in_substitutions":       false,
 		"allow_token_displayname":            false,
 		"country":                            []interface{}{},
 		"not_before_bound":                   "permit",
diff --git a/builtin/logical/pki/cert_util.go b/builtin/logical/pki/cert_util.go
index 9429c850f4b0b42420d5ffd892359c3178185bfb..7fabd16effcc4a7f57178c26f23fbf789b584de6 100644
--- a/builtin/logical/pki/cert_util.go
+++ b/builtin/logical/pki/cert_util.go
@@ -30,6 +30,7 @@ import (
 	"github.com/openbao/openbao/sdk/v2/framework"
 	"github.com/openbao/openbao/sdk/v2/helper/certutil"
 	"github.com/openbao/openbao/sdk/v2/helper/errutil"
+	"github.com/openbao/openbao/sdk/v2/helper/identitytpl"
 	"github.com/openbao/openbao/sdk/v2/logical"
 	"github.com/ryanuber/go-glob"
 	"golang.org/x/crypto/cryptobyte"
@@ -272,11 +273,31 @@ func validateURISAN(b *backend, data *inputBundle, uri string) bool {
 		if data.role.AllowedURISANsTemplate {
 			isTemplate, _ := framework.ValidateIdentityTemplate(allowed)
 			if isTemplate && data.req.EntityID != "" {
-				tmpAllowed, err := framework.PopulateIdentityTemplate(allowed, data.req.EntityID, b.System())
+				entity, err := b.System().EntityInfo(data.req.EntityID)
+				if err != nil || entity == nil {
+					continue
+				}
+
+				groups, err := b.System().GroupsForEntity(data.req.EntityID)
+				if err != nil {
+					continue
+				}
+
+				input := identitytpl.PopulateStringInput{
+					String: allowed,
+					Entity: entity,
+					Groups: groups,
+					Mode:   identitytpl.ACLTemplating,
+				}
+
+				if !data.role.AllowGlobsInSubstitutions {
+					input.BlockedSubstitutions = []string{"*"}
+				}
+
+				_, allowed, err = identitytpl.PopulateString(input)
 				if err != nil {
 					continue
 				}
-				allowed = tmpAllowed
 			}
 		}
 		validURI := glob.Glob(allowed, uri)
@@ -564,12 +585,31 @@ func validateNames(b *backend, data *inputBundle, names []string) string {
 				if data.role.AllowedDomainsTemplate {
 					isTemplate, _ := framework.ValidateIdentityTemplate(currDomain)
 					if isTemplate && data.req.EntityID != "" {
-						tmpCurrDomain, err := framework.PopulateIdentityTemplate(currDomain, data.req.EntityID, b.System())
+						entity, err := b.System().EntityInfo(data.req.EntityID)
+						if err != nil || entity == nil {
+							continue
+						}
+
+						groups, err := b.System().GroupsForEntity(data.req.EntityID)
 						if err != nil {
 							continue
 						}
 
-						currDomain = tmpCurrDomain
+						input := identitytpl.PopulateStringInput{
+							String: currDomain,
+							Entity: entity,
+							Groups: groups,
+							Mode:   identitytpl.ACLTemplating,
+						}
+
+						if !data.role.AllowGlobsInSubstitutions {
+							input.BlockedSubstitutions = []string{"*"}
+						}
+
+						_, currDomain, err = identitytpl.PopulateString(input)
+						if err != nil {
+							continue
+						}
 					}
 				}
 
diff --git a/builtin/logical/pki/path_roles.go b/builtin/logical/pki/path_roles.go
index b96d869a00560fbfe2409e759130dd670611831d..04c66bbadab47f199839027692f5ade4623c329d 100644
--- a/builtin/logical/pki/path_roles.go
+++ b/builtin/logical/pki/path_roles.go
@@ -114,6 +114,15 @@ accepts a comma-separated string or list of domains.`,
 			Description: `If set, Allowed domains can be specified using identity template policies.
 				Non-templated domains are also permitted.`,
 		},
+		"allow_globs_in_substitutions": {
+			Type:     framework.TypeBool,
+			Required: true,
+			Description: `If set and templating is enabled, the values substituted in
+				for allowed_uri_sans_template and allowed_domains template expression
+				might contain a wildcard characters ('*' and '+'). This can enable
+				injection attacks. Only use this, if the data used by the templates
+				is trusted.`,
+		},
 		"allow_bare_domains": {
 			Type:     framework.TypeBool,
 			Required: true,
@@ -507,6 +516,15 @@ accepts a comma-separated string or list of domains.`,
 				Non-templated domains are also permitted.`,
 				Default: false,
 			},
+			"allow_globs_in_substitutions": {
+				Type: framework.TypeBool,
+				Description: `If set and templating is enabled, the values substituted in
+					for allowed_uri_sans_template and allowed_domains template expression
+					might contain a wildcard characters ('*' and '+'). This can enable
+					injection attacks. Only use this, if the data used by the templates
+					is trusted.`,
+				Default: false,
+			},
 			"allow_bare_domains": {
 				Type: framework.TypeBool,
 				Description: `If set, clients can request certificates
@@ -1142,6 +1160,7 @@ func (b *backend) pathRoleCreate(ctx context.Context, req *logical.Request, data
 		AllowLocalhost:                data.Get("allow_localhost").(bool),
 		AllowedDomains:                data.Get("allowed_domains").([]string),
 		AllowedDomainsTemplate:        data.Get("allowed_domains_template").(bool),
+		AllowGlobsInSubstitutions:     data.Get("allow_globs_in_substitutions").(bool),
 		AllowBareDomains:              data.Get("allow_bare_domains").(bool),
 		AllowSubdomains:               data.Get("allow_subdomains").(bool),
 		AllowGlobDomains:              data.Get("allow_glob_domains").(bool),
@@ -1395,6 +1414,7 @@ func (b *backend) pathRolePatch(ctx context.Context, req *logical.Request, data
 		AllowLocalhost:                data.GetWithExplicitDefault("allow_localhost", oldEntry.AllowLocalhost).(bool),
 		AllowedDomains:                data.GetWithExplicitDefault("allowed_domains", oldEntry.AllowedDomains).([]string),
 		AllowedDomainsTemplate:        data.GetWithExplicitDefault("allowed_domains_template", oldEntry.AllowedDomainsTemplate).(bool),
+		AllowGlobsInSubstitutions:     data.GetWithExplicitDefault("allow_globs_in_substitutions", oldEntry.AllowGlobsInSubstitutions).(bool),
 		AllowBareDomains:              data.GetWithExplicitDefault("allow_bare_domains", oldEntry.AllowBareDomains).(bool),
 		AllowSubdomains:               data.GetWithExplicitDefault("allow_subdomains", oldEntry.AllowSubdomains).(bool),
 		AllowGlobDomains:              data.GetWithExplicitDefault("allow_glob_domains", oldEntry.AllowGlobDomains).(bool),
@@ -1635,6 +1655,7 @@ type roleEntry struct {
 	AllowedDomainsOld             string        `json:"allowed_domains,omitempty"`
 	AllowedDomains                []string      `json:"allowed_domains_list"`
 	AllowedDomainsTemplate        bool          `json:"allowed_domains_template"`
+	AllowGlobsInSubstitutions     bool          `json:"allow_globs_in_substitutions"`
 	AllowBaseDomain               bool          `json:"allow_base_domain"`
 	AllowBareDomains              bool          `json:"allow_bare_domains"`
 	AllowTokenDisplayName         bool          `json:"allow_token_displayname"`
@@ -1703,6 +1724,7 @@ func (r *roleEntry) ToResponseData() map[string]interface{} {
 		"allow_localhost":                    r.AllowLocalhost,
 		"allowed_domains":                    r.AllowedDomains,
 		"allowed_domains_template":           r.AllowedDomainsTemplate,
+		"allow_globs_in_substitutions":       r.AllowGlobsInSubstitutions,
 		"allow_bare_domains":                 r.AllowBareDomains,
 		"allow_token_displayname":            r.AllowTokenDisplayName,
 		"allow_subdomains":                   r.AllowSubdomains,
diff --git a/builtin/logical/ssh/backend_test.go b/builtin/logical/ssh/backend_test.go
index 28cad1a771ea186c2c40b29973fe35a2ad4d2a0e..9e0c9aa330416f7589879aaacec621b0c2de5c98 100644
--- a/builtin/logical/ssh/backend_test.go
+++ b/builtin/logical/ssh/backend_test.go
@@ -374,6 +374,7 @@ func TestBackend_AllowedUsersTemplate(t *testing.T) {
 		testUserName, map[string]string{
 			"ssh_username": testUserName,
 		},
+		false,
 	)
 }
 
@@ -384,6 +385,7 @@ func TestBackend_MultipleAllowedUsersTemplate(t *testing.T) {
 		testUserName, map[string]string{
 			"ssh_username": testMultiUserName,
 		},
+		true,
 	)
 }
 
@@ -394,6 +396,7 @@ func TestBackend_AllowedUsersTemplate_WithStaticPrefix(t *testing.T) {
 		"ssh-"+testUserName, map[string]string{
 			"ssh_username": testUserName,
 		},
+		false,
 	)
 }
 
@@ -419,6 +422,56 @@ func TestBackend_DefaultUserTemplate_WithStaticPrefix(t *testing.T) {
 	)
 }
 
+func TestBackend_ForbiddenCommaInTemplate(t *testing.T) {
+	cluster, userpassToken := getSshCaTestCluster(t, testUserName)
+	defer cluster.Cleanup()
+	client := cluster.Cores[0].Client
+
+	// set metadata "ssh_username" to userpass username
+	tokenLookupResponse, err := client.Logical().Write("/auth/token/lookup", map[string]interface{}{
+		"token": userpassToken,
+	})
+	if err != nil {
+		t.Fatal(err)
+	}
+	entityID := tokenLookupResponse.Data["entity_id"].(string)
+	_, err = client.Logical().Write("/identity/entity/id/"+entityID, map[string]interface{}{
+		"metadata": map[string]string{
+			"ssh_username": testMultiUserName,
+		},
+	})
+	if err != nil {
+		t.Fatal(err)
+	}
+
+	_, err = client.Logical().Write("ssh/roles/my-role", map[string]interface{}{
+		"key_type":                      testCaKeyType,
+		"allow_user_certificates":       true,
+		"default_user":                  "{{identity.entity.metadata.ssh_username}}",
+		"default_user_template":         true,
+		"allowed_users":                 "{{identity.entity.metadata.ssh_username}}",
+		"allowed_users_template":        true,
+		"allow_commas_in_substitutions": false,
+	})
+	if err != nil {
+		t.Fatal(err)
+	}
+
+	// sign SSH key as userpass user
+	client.SetToken(userpassToken)
+	_, err = client.Logical().Write("ssh/sign/my-role", map[string]interface{}{
+		"public_key": testCAPublicKey,
+	})
+	if err == nil {
+		t.Error("signing request should fail when default_user is not in the allowed_users list, because allowed_users_template is true and default_user_template is not")
+	}
+
+	expectedErrStr := `template '{{identity.entity.metadata.ssh_username}}' could not be rendered -> template substitution contains forbidden value ","`
+	if !strings.Contains(err.Error(), expectedErrStr) {
+		t.Errorf("expected error to include %q but it was: %q", expectedErrStr, err.Error())
+	}
+}
+
 func TestBackend_DefaultUserTemplateFalse_AllowedUsersTemplateTrue(t *testing.T) {
 	cluster, userpassToken := getSshCaTestCluster(t, testUserName)
 	defer cluster.Cleanup()
@@ -1959,15 +2012,17 @@ func testAllowedPrincipalsTemplate(t *testing.T, testAllowedDomainsTemplate stri
 
 func testAllowedUsersTemplate(t *testing.T, testAllowedUsersTemplate string,
 	expectedValidPrincipal string, testEntityMetadata map[string]string,
+	allowCommasInSubstitutions bool,
 ) {
 	testAllowedPrincipalsTemplate(
 		t, testAllowedUsersTemplate,
 		expectedValidPrincipal, testEntityMetadata,
 		map[string]interface{}{
-			"key_type":                testCaKeyType,
-			"allow_user_certificates": true,
-			"allowed_users":           testAllowedUsersTemplate,
-			"allowed_users_template":  true,
+			"key_type":                      testCaKeyType,
+			"allow_user_certificates":       true,
+			"allowed_users":                 testAllowedUsersTemplate,
+			"allowed_users_template":        true,
+			"allow_commas_in_substitutions": allowCommasInSubstitutions,
 		},
 		map[string]interface{}{
 			"public_key":       testCAPublicKey,
diff --git a/builtin/logical/ssh/path_issue_sign.go b/builtin/logical/ssh/path_issue_sign.go
index d85677bf6c8324a5242632cb6dcc70fe559d4199..6a8d234297415b210e7cf1c17ce5d28c5f7ad334 100644
--- a/builtin/logical/ssh/path_issue_sign.go
+++ b/builtin/logical/ssh/path_issue_sign.go
@@ -23,6 +23,7 @@ import (
 	"github.com/hashicorp/go-secure-stdlib/strutil"
 	"github.com/openbao/openbao/sdk/v2/framework"
 	"github.com/openbao/openbao/sdk/v2/helper/certutil"
+	"github.com/openbao/openbao/sdk/v2/helper/identitytpl"
 	"github.com/openbao/openbao/sdk/v2/logical"
 	"golang.org/x/crypto/ssh"
 )
@@ -79,7 +80,7 @@ func (b *backend) pathSignIssueCertificateHelper(sc *storageContext, req *logica
 	} else {
 		defaultPrincipal := role.DefaultUser
 		if role.DefaultUserTemplate {
-			defaultPrincipal, err = b.renderPrincipal(role.DefaultUser, req)
+			defaultPrincipal, err = b.renderPrincipal(role.DefaultUser, req, true)
 			if err != nil {
 				return nil, err
 			}
@@ -163,21 +164,48 @@ func (b *backend) pathSignIssueCertificateHelper(sc *storageContext, req *logica
 	return response, nil
 }
 
-func (b *backend) renderPrincipal(principal string, req *logical.Request) (string, error) {
+func (b *backend) renderPrincipal(principal string, req *logical.Request, allowCommasInSubstitutions bool) (string, error) {
+	if req.EntityID == "" {
+		return principal, nil
+	}
+
 	// Look for templating markers {{ .* }}
 	matched := containsTemplateRegex.MatchString(principal)
-	if matched {
-		if req.EntityID != "" {
-			// Retrieve principal based on template + entityID from request.
-			renderedPrincipal, err := framework.PopulateIdentityTemplate(principal, req.EntityID, b.System())
-			if err != nil {
-				return "", fmt.Errorf("template '%s' could not be rendered -> %s", principal, err)
-			}
-			return renderedPrincipal, nil
-		}
+	if !matched {
+		// Static principal
+		return principal, nil
 	}
-	// Static principal
-	return principal, nil
+
+	// Retrieve principal based on template + entityID from request.
+	entity, err := b.System().EntityInfo(req.EntityID)
+	if err != nil {
+		return "", err
+	}
+	if entity == nil {
+		return "", errors.New("no entity found")
+	}
+
+	groups, err := b.System().GroupsForEntity(req.EntityID)
+	if err != nil {
+		return "", err
+	}
+
+	input := identitytpl.PopulateStringInput{
+		String: principal,
+		Entity: entity,
+		Groups: groups,
+		Mode:   identitytpl.ACLTemplating,
+	}
+	if !allowCommasInSubstitutions {
+		input.BlockedSubstitutions = []string{","}
+	}
+
+	_, renderedPrincipal, err := identitytpl.PopulateString(input)
+	if err != nil {
+		return "", fmt.Errorf("template '%s' could not be rendered -> %s", principal, err)
+	}
+
+	return renderedPrincipal, nil
 }
 
 func (b *backend) calculateValidPrincipals(data *framework.FieldData, req *logical.Request, role *sshRole, defaultPrincipal, principalsAllowedByRole string, enableTemplating bool, validatePrincipal func([]string, string) bool) ([]string, error) {
@@ -193,7 +221,7 @@ func (b *backend) calculateValidPrincipals(data *framework.FieldData, req *logic
 	// Build list of allowed Principals from template and static principalsAllowedByRole
 	var allowedPrincipals []string
 	if enableTemplating {
-		rendered, err := b.renderPrincipal(principalsAllowedByRole, req)
+		rendered, err := b.renderPrincipal(principalsAllowedByRole, req, role.AllowCommasInSubstitutions)
 		if err != nil {
 			return nil, err
 		}
@@ -321,7 +349,7 @@ func (b *backend) calculateCriticalOptions(data *framework.FieldData, role *sshR
 }
 
 func (b *backend) calculateExtensions(data *framework.FieldData, req *logical.Request, role *sshRole) (map[string]string, bool, error) {
-	unparsedExtensions := data.Get("extensions").(map[string]interface{})
+	unparsedExtensions := data.Get("extensions").(map[string]any)
 	extensions := make(map[string]string)
 
 	if len(unparsedExtensions) > 0 {
@@ -345,32 +373,58 @@ func (b *backend) calculateExtensions(data *framework.FieldData, req *logical.Re
 		return extensions, false, nil
 	}
 
+	if !role.DefaultExtensionsTemplate {
+		return role.DefaultExtensions, false, nil
+	}
+
 	haveMissingEntityInfoWithTemplatedExt := false
+	var (
+		// entity and groups are lazy loaded
+		entity *logical.Entity
+		groups []*logical.Group
+		err    error
+	)
+
+	for extensionKey, extensionValue := range role.DefaultExtensions {
+		// Look for templating markers {{ .* }}
+		matched := containsTemplateRegex.MatchString(extensionValue)
+		if !matched {
+			// Static extension value or err template
+			extensions[extensionKey] = extensionValue
+			continue
+		}
 
-	if role.DefaultExtensionsTemplate {
-		for extensionKey, extensionValue := range role.DefaultExtensions {
-			// Look for templating markers {{ .* }}
-			matched := containsTemplateRegex.MatchString(extensionValue)
-			if matched {
-				if req.EntityID != "" {
-					// Retrieve extension value based on template + entityID from request.
-					templateExtensionValue, err := framework.PopulateIdentityTemplate(extensionValue, req.EntityID, b.System())
-					if err == nil {
-						// Template returned an extension value that we can use
-						extensions[extensionKey] = templateExtensionValue
-					} else {
-						return nil, false, fmt.Errorf("template '%s' could not be rendered -> %s", extensionValue, err)
-					}
-				} else {
-					haveMissingEntityInfoWithTemplatedExt = true
-				}
-			} else {
-				// Static extension value or err template
-				extensions[extensionKey] = extensionValue
+		if req.EntityID == "" {
+			haveMissingEntityInfoWithTemplatedExt = true
+			continue
+		}
+
+		// Retrieve extension value based on template + entityID from request.
+		if entity == nil {
+			entity, err = b.System().EntityInfo(req.EntityID)
+			if err != nil {
+				return nil, false, err
+			}
+			if entity == nil {
+				return nil, false, errors.New("no entity found")
+			}
+
+			groups, err = b.System().GroupsForEntity(req.EntityID)
+			if err != nil {
+				return nil, false, err
 			}
 		}
-	} else {
-		extensions = role.DefaultExtensions
+
+		input := identitytpl.PopulateStringInput{
+			String: extensionValue,
+			Entity: entity,
+			Groups: groups,
+			Mode:   identitytpl.ACLTemplating,
+		}
+		_, extensions[extensionKey], err = identitytpl.PopulateString(input)
+		if err != nil {
+			return nil, false, fmt.Errorf("template '%s' could not be rendered -> %s", extensionValue, err)
+		}
 	}
 
 	return extensions, haveMissingEntityInfoWithTemplatedExt, nil
diff --git a/builtin/logical/ssh/path_roles.go b/builtin/logical/ssh/path_roles.go
index bf2be7dbaeed40eef4149ef32c2b7198c3a687a4..61ce503839e68bccc64db8b0e64452d741a761ba 100644
--- a/builtin/logical/ssh/path_roles.go
+++ b/builtin/logical/ssh/path_roles.go
@@ -62,6 +62,7 @@ type sshRole struct {
 	AllowSubdomains            bool              `mapstructure:"allow_subdomains" json:"allow_subdomains"`
 	AllowUserKeyIDs            bool              `mapstructure:"allow_user_key_ids" json:"allow_user_key_ids"`
 	AllowEmptyPrincipals       bool              `mapstructure:"allow_empty_principals" json:"allow_empty_principals"`
+	AllowCommasInSubstitutions bool              `mapstructure:"allow_commas_in_substitutions" json:"allow_commas_in_substitutions"`
 	KeyIDFormat                string            `mapstructure:"key_id_format" json:"key_id_format"`
 	OldAllowedUserKeyLengths   map[string]int    `mapstructure:"allowed_user_key_lengths" json:"allowed_user_key_lengths,omitempty"`
 	AllowedUserKeyTypesLengths map[string][]int  `mapstructure:"allowed_user_key_types_lengths" json:"allowed_user_key_types_lengths"`
@@ -379,6 +380,21 @@ func pathRoles(b *backend) *framework.Path {
 					Value: 30,
 				},
 			},
+			"allow_commas_in_substitutions": {
+				Type: framework.TypeBool,
+				Description: `
+				If true and templating is enabled, the values substituted in for
+				allowed_users and allowed_domains template expressions might contain a
+				comma (','). As these values are comma separated lists, this can enable
+				injection attacks. Only use this, if the data used by the templates is
+				trusted.`,
+				Default: false,
+				DisplayAttrs: &framework.DisplayAttributes{
+					Name:  "Allow Commas in Substitutions",
+					Value: false,
+				},
+			},
+
 			"allow_empty_principals": {
 				Type: framework.TypeBool,
 				Description: `
@@ -524,27 +540,28 @@ func (b *backend) createCARole(allowedUsers, defaultUser, signer string, data *f
 	ttl := time.Duration(data.Get("ttl").(int)) * time.Second
 	maxTTL := time.Duration(data.Get("max_ttl").(int)) * time.Second
 	role := &sshRole{
-		AllowedCriticalOptions:    data.Get("allowed_critical_options").(string),
-		AllowedExtensions:         data.Get("allowed_extensions").(string),
-		AllowUserCertificates:     data.Get("allow_user_certificates").(bool),
-		AllowHostCertificates:     data.Get("allow_host_certificates").(bool),
-		AllowedUsers:              allowedUsers,
-		AllowedUsersTemplate:      data.Get("allowed_users_template").(bool),
-		AllowedDomains:            data.Get("allowed_domains").(string),
-		AllowedDomainsTemplate:    data.Get("allowed_domains_template").(bool),
-		DefaultUser:               defaultUser,
-		DefaultUserTemplate:       data.Get("default_user_template").(bool),
-		AllowBareDomains:          data.Get("allow_bare_domains").(bool),
-		AllowSubdomains:           data.Get("allow_subdomains").(bool),
-		AllowUserKeyIDs:           data.Get("allow_user_key_ids").(bool),
-		AllowEmptyPrincipals:      data.Get("allow_empty_principals").(bool),
-		DefaultExtensionsTemplate: data.Get("default_extensions_template").(bool),
-		KeyIDFormat:               data.Get("key_id_format").(string),
-		KeyType:                   KeyTypeCA,
-		AlgorithmSigner:           signer,
-		Version:                   roleEntryVersion,
-		NotBeforeDuration:         time.Duration(data.Get("not_before_duration").(int)) * time.Second,
-		Issuer:                    data.Get("issuer_ref").(string),
+		AllowedCriticalOptions:     data.Get("allowed_critical_options").(string),
+		AllowedExtensions:          data.Get("allowed_extensions").(string),
+		AllowUserCertificates:      data.Get("allow_user_certificates").(bool),
+		AllowHostCertificates:      data.Get("allow_host_certificates").(bool),
+		AllowedUsers:               allowedUsers,
+		AllowedUsersTemplate:       data.Get("allowed_users_template").(bool),
+		AllowedDomains:             data.Get("allowed_domains").(string),
+		AllowedDomainsTemplate:     data.Get("allowed_domains_template").(bool),
+		DefaultUser:                defaultUser,
+		DefaultUserTemplate:        data.Get("default_user_template").(bool),
+		AllowBareDomains:           data.Get("allow_bare_domains").(bool),
+		AllowSubdomains:            data.Get("allow_subdomains").(bool),
+		AllowUserKeyIDs:            data.Get("allow_user_key_ids").(bool),
+		AllowCommasInSubstitutions: data.Get("allow_commas_in_substitutions").(bool),
+		AllowEmptyPrincipals:       data.Get("allow_empty_principals").(bool),
+		DefaultExtensionsTemplate:  data.Get("default_extensions_template").(bool),
+		KeyIDFormat:                data.Get("key_id_format").(string),
+		KeyType:                    KeyTypeCA,
+		AlgorithmSigner:            signer,
+		Version:                    roleEntryVersion,
+		NotBeforeDuration:          time.Duration(data.Get("not_before_duration").(int)) * time.Second,
+		Issuer:                     data.Get("issuer_ref").(string),
 	}
 
 	if !role.AllowUserCertificates && !role.AllowHostCertificates {
@@ -728,31 +745,32 @@ func (b *backend) parseRole(role *sshRole) (map[string]interface{}, error) {
 		}
 
 		result = map[string]interface{}{
-			"allowed_users":               role.AllowedUsers,
-			"allowed_users_template":      role.AllowedUsersTemplate,
-			"allowed_domains":             role.AllowedDomains,
-			"allowed_domains_template":    role.AllowedDomainsTemplate,
-			"default_user":                role.DefaultUser,
-			"default_user_template":       role.DefaultUserTemplate,
-			"ttl":                         int64(ttl.Seconds()),
-			"max_ttl":                     int64(maxTTL.Seconds()),
-			"allowed_critical_options":    role.AllowedCriticalOptions,
-			"allowed_extensions":          role.AllowedExtensions,
-			"allow_user_certificates":     role.AllowUserCertificates,
-			"allow_host_certificates":     role.AllowHostCertificates,
-			"allow_bare_domains":          role.AllowBareDomains,
-			"allow_subdomains":            role.AllowSubdomains,
-			"allow_user_key_ids":          role.AllowUserKeyIDs,
-			"allow_empty_principals":      role.AllowEmptyPrincipals,
-			"key_id_format":               role.KeyIDFormat,
-			"key_type":                    role.KeyType,
-			"default_critical_options":    role.DefaultCriticalOptions,
-			"default_extensions":          role.DefaultExtensions,
-			"default_extensions_template": role.DefaultExtensionsTemplate,
-			"allowed_user_key_lengths":    role.AllowedUserKeyTypesLengths,
-			"algorithm_signer":            role.AlgorithmSigner,
-			"not_before_duration":         int64(role.NotBeforeDuration.Seconds()),
-			"issuer_ref":                  role.Issuer,
+			"allowed_users":                 role.AllowedUsers,
+			"allowed_users_template":        role.AllowedUsersTemplate,
+			"allowed_domains":               role.AllowedDomains,
+			"allowed_domains_template":      role.AllowedDomainsTemplate,
+			"default_user":                  role.DefaultUser,
+			"default_user_template":         role.DefaultUserTemplate,
+			"ttl":                           int64(ttl.Seconds()),
+			"max_ttl":                       int64(maxTTL.Seconds()),
+			"allowed_critical_options":      role.AllowedCriticalOptions,
+			"allowed_extensions":            role.AllowedExtensions,
+			"allow_user_certificates":       role.AllowUserCertificates,
+			"allow_host_certificates":       role.AllowHostCertificates,
+			"allow_bare_domains":            role.AllowBareDomains,
+			"allow_subdomains":              role.AllowSubdomains,
+			"allow_user_key_ids":            role.AllowUserKeyIDs,
+			"allow_commas_in_substitutions": role.AllowCommasInSubstitutions,
+			"allow_empty_principals":        role.AllowEmptyPrincipals,
+			"key_id_format":                 role.KeyIDFormat,
+			"key_type":                      role.KeyType,
+			"default_critical_options":      role.DefaultCriticalOptions,
+			"default_extensions":            role.DefaultExtensions,
+			"default_extensions_template":   role.DefaultExtensionsTemplate,
+			"allowed_user_key_lengths":      role.AllowedUserKeyTypesLengths,
+			"algorithm_signer":              role.AlgorithmSigner,
+			"not_before_duration":           int64(role.NotBeforeDuration.Seconds()),
+			"issuer_ref":                    role.Issuer,
 		}
 	case KeyTypeDynamic:
 		return nil, errors.New("dynamic key type roles are no longer supported")
diff --git a/changelog/3401.txt b/changelog/3401.txt
new file mode 100644
index 0000000000000000000000000000000000000000..c93160bdad698f52064ef628e3adfc6b63e22762
--- /dev/null
+++ b/changelog/3401.txt
@@ -0,0 +1,12 @@
+```release-note:security
+core/policies: If the value of a template expression contains a `+` or `*` character it will now be rejected by default. Set `allow_wildcards_in_substitutions = true` to overwrite. GHSA-59w7-v8rr-pr4p.
+```
+```release-note:security
+core/policies: If the value of a template expression contains a `/` character it will now be rejected by default. Set `allow_slashes_in_substitutions = true` to overwrite. GHSA-59w7-v8rr-pr4p.
+```
+```release-note:security
+secret/pki: If the value of a template expression in `allowed_uri_sans_template` and `allowed_domains` contains a `*` character it will now be rejected by default. Set `allow_globs_in_substitutions = true` to overwrite. GHSA-59w7-v8rr-pr4p.
+```
+```release-note:security
+secret/ssh: If the value of a template expression in `allowed_users` or `allowed_domains` contains a `,` character it will now be rejected by default. Set `allow_commas_in_substitutions = true` to overwrite. GHSA-59w7-v8rr-pr4p.
+```
diff --git a/http/sys_policy_test.go b/http/sys_policy_test.go
index 0dba3dd8078ac9ce07ea02581d2b12dd840cd3c8..073b9cb9ca620a7f516b27e5ce2fcd7b5764aed6 100644
--- a/http/sys_policy_test.go
+++ b/http/sys_policy_test.go
@@ -20,20 +20,20 @@ func TestSysPolicies(t *testing.T) {
 
 	resp := testHttpGet(t, token, addr+"/v1/sys/policy")
 
-	var actual map[string]interface{}
-	expected := map[string]interface{}{
+	var actual map[string]any
+	expected := map[string]any{
 		"lease_id":       "",
 		"renewable":      false,
 		"lease_duration": json.Number("0"),
 		"wrap_info":      nil,
 		"warnings":       nil,
 		"auth":           nil,
-		"data": map[string]interface{}{
-			"policies": []interface{}{"default", "root"},
-			"keys":     []interface{}{"default", "root"},
+		"data": map[string]any{
+			"policies": []any{"default", "root"},
+			"keys":     []any{"default", "root"},
 		},
-		"policies": []interface{}{"default", "root"},
-		"keys":     []interface{}{"default", "root"},
+		"policies": []any{"default", "root"},
+		"keys":     []any{"default", "root"},
 	}
 	testResponseStatus(t, resp, 200)
 	testResponseBody(t, resp, &actual)
@@ -51,24 +51,28 @@ func TestSysReadPolicy(t *testing.T) {
 
 	resp := testHttpGet(t, token, addr+"/v1/sys/policy/root")
 
-	var actual map[string]interface{}
-	expected := map[string]interface{}{
+	var actual map[string]any
+	expected := map[string]any{
 		"lease_id":       "",
 		"renewable":      false,
 		"lease_duration": json.Number("0"),
 		"wrap_info":      nil,
 		"warnings":       nil,
 		"auth":           nil,
-		"data": map[string]interface{}{
-			"name":         "root",
-			"rules":        "",
-			"cas_required": false,
-			"version":      json.Number("0"),
+		"data": map[string]any{
+			"name":                             "root",
+			"rules":                            "",
+			"cas_required":                     false,
+			"version":                          json.Number("0"),
+			"allow_slashes_in_substitutions":   false,
+			"allow_wildcards_in_substitutions": false,
 		},
-		"name":         "root",
-		"rules":        "",
-		"cas_required": false,
-		"version":      json.Number("0"),
+		"name":                             "root",
+		"rules":                            "",
+		"cas_required":                     false,
+		"version":                          json.Number("0"),
+		"allow_slashes_in_substitutions":   false,
+		"allow_wildcards_in_substitutions": false,
 	}
 	testResponseStatus(t, resp, 200)
 	testResponseBody(t, resp, &actual)
@@ -84,27 +88,27 @@ func TestSysWritePolicy(t *testing.T) {
 	defer ln.Close()
 	TestServerAuth(t, addr, token)
 
-	resp := testHttpPost(t, token, addr+"/v1/sys/policy/foo", map[string]interface{}{
+	resp := testHttpPost(t, token, addr+"/v1/sys/policy/foo", map[string]any{
 		"rules": `path "*" { capabilities = ["read"] }`,
 	})
 	testResponseStatus(t, resp, 200)
 
 	resp = testHttpGet(t, token, addr+"/v1/sys/policy")
 
-	var actual map[string]interface{}
-	expected := map[string]interface{}{
+	var actual map[string]any
+	expected := map[string]any{
 		"lease_id":       "",
 		"renewable":      false,
 		"lease_duration": json.Number("0"),
 		"wrap_info":      nil,
 		"warnings":       nil,
 		"auth":           nil,
-		"data": map[string]interface{}{
-			"policies": []interface{}{"default", "foo", "root"},
-			"keys":     []interface{}{"default", "foo", "root"},
+		"data": map[string]any{
+			"policies": []any{"default", "foo", "root"},
+			"keys":     []any{"default", "foo", "root"},
 		},
-		"policies": []interface{}{"default", "foo", "root"},
-		"keys":     []interface{}{"default", "foo", "root"},
+		"policies": []any{"default", "foo", "root"},
+		"keys":     []any{"default", "foo", "root"},
 	}
 	testResponseStatus(t, resp, 200)
 	testResponseBody(t, resp, &actual)
@@ -113,7 +117,7 @@ func TestSysWritePolicy(t *testing.T) {
 		t.Fatalf("bad: got\n%#v\nexpected\n%#v\n", actual, expected)
 	}
 
-	resp = testHttpPost(t, token, addr+"/v1/sys/policy/response-wrapping", map[string]interface{}{
+	resp = testHttpPost(t, token, addr+"/v1/sys/policy/response-wrapping", map[string]any{
 		"rules": ``,
 	})
 	testResponseStatus(t, resp, 400)
@@ -125,7 +129,7 @@ func TestSysDeletePolicy(t *testing.T) {
 	defer ln.Close()
 	TestServerAuth(t, addr, token)
 
-	resp := testHttpPost(t, token, addr+"/v1/sys/policy/foo", map[string]interface{}{
+	resp := testHttpPost(t, token, addr+"/v1/sys/policy/foo", map[string]any{
 		"rules": `path "*" { capabilities = ["read"] }`,
 	})
 	testResponseStatus(t, resp, 200)
@@ -140,20 +144,20 @@ func TestSysDeletePolicy(t *testing.T) {
 
 	resp = testHttpGet(t, token, addr+"/v1/sys/policy")
 
-	var actual map[string]interface{}
-	expected := map[string]interface{}{
+	var actual map[string]any
+	expected := map[string]any{
 		"lease_id":       "",
 		"renewable":      false,
 		"lease_duration": json.Number("0"),
 		"wrap_info":      nil,
 		"warnings":       nil,
 		"auth":           nil,
-		"data": map[string]interface{}{
-			"policies": []interface{}{"default", "root"},
-			"keys":     []interface{}{"default", "root"},
+		"data": map[string]any{
+			"policies": []any{"default", "root"},
+			"keys":     []any{"default", "root"},
 		},
-		"policies": []interface{}{"default", "root"},
-		"keys":     []interface{}{"default", "root"},
+		"policies": []any{"default", "root"},
+		"keys":     []any{"default", "root"},
 	}
 	testResponseStatus(t, resp, 200)
 	testResponseBody(t, resp, &actual)
diff --git a/sdk/framework/identity.go b/sdk/framework/identity.go
index f32f02ddd40e1444b17788f313949768455dd5bd..a268c84388fe3c81e62236273e04e0a801c12a24 100644
--- a/sdk/framework/identity.go
+++ b/sdk/framework/identity.go
@@ -15,6 +15,9 @@ import (
 // instance of system view. It will query system view for information about the
 // entity and use the resulting identity information to populate the template
 // string.
+//
+// Deprecated: This function does not expose all options of
+// [identitytpl.PopulateString] consider inlining
 func PopulateIdentityTemplate(tpl string, entityID string, sysView logical.SystemView) (string, error) {
 	entity, err := sysView.EntityInfo(entityID)
 	if err != nil {
diff --git a/sdk/helper/identitytpl/templating.go b/sdk/helper/identitytpl/templating.go
index 214af79dca924993cdd65d72451bbd9b4d74a599..9b96e0f47808c1ee5ca3f87eb59ffd9159b44a2e 100644
--- a/sdk/helper/identitytpl/templating.go
+++ b/sdk/helper/identitytpl/templating.go
@@ -20,6 +20,7 @@ var (
 	ErrNoEntityAttachedToToken       = errors.New("string contains entity template directives but no entity was provided")
 	ErrNoGroupsAttachedToToken       = errors.New("string contains groups template directives but no groups were provided")
 	ErrTemplateValueNotFound         = errors.New("no value could be found for one of the template directives")
+	ErrTemplateWildcard              = `template substitution contains forbidden value %q`
 )
 
 const (
@@ -28,13 +29,14 @@ const (
 )
 
 type PopulateStringInput struct {
-	String            string
-	ValidityCheckOnly bool
-	Entity            *logical.Entity
-	Groups            []*logical.Group
-	NamespaceID       string
-	Mode              int       // processing mode, ACLTemplate or JSONTemplating
-	Now               time.Time // optional, defaults to current time
+	String               string
+	ValidityCheckOnly    bool
+	Entity               *logical.Entity
+	Groups               []*logical.Group
+	NamespaceID          string
+	Mode                 int       // processing mode, ACLTemplate or JSONTemplating
+	Now                  time.Time // optional, defaults to current time
+	BlockedSubstitutions []string  // optional, defaults to ["*", "+"] if (.Mode == ACLTemplate) and [] otherwise
 
 	templateHandler templateHandlerFunc
 	groupIDs        []string
@@ -155,6 +157,11 @@ func PopulateString(p PopulateStringInput) (bool, string, error) {
 				if err != nil {
 					return false, "", err
 				}
+				for _, blocked := range p.BlockedSubstitutions {
+					if strings.Contains(tmplStr, blocked) {
+						return false, "", fmt.Errorf(ErrTemplateWildcard, blocked)
+					}
+				}
 				b.WriteString(tmplStr)
 				b.WriteString(splitPiece[1])
 			}
diff --git a/sdk/helper/identitytpl/templating_test.go b/sdk/helper/identitytpl/templating_test.go
index 5ab4d66709be56cae3c3f989efc09ca888e61675..47f1da9ce595c42323e10ac0b048840989b10cef 100644
--- a/sdk/helper/identitytpl/templating_test.go
+++ b/sdk/helper/identitytpl/templating_test.go
@@ -20,24 +20,25 @@ var testNow = time.Now().Add(100 * time.Hour)
 
 func TestPopulate_Basic(t *testing.T) {
 	tests := []struct {
-		mode                int
-		name                string
-		input               string
-		output              string
-		err                 error
-		entityName          string
-		metadata            map[string]string
-		aliasAccessor       string
-		aliasID             string
-		aliasName           string
-		nilEntity           bool
-		validityCheckOnly   bool
-		aliasMetadata       map[string]string
-		aliasCustomMetadata map[string]string
-		groupName           string
-		groupMetadata       map[string]string
-		groupMemberships    []string
-		now                 time.Time
+		mode                 int
+		name                 string
+		input                string
+		blockedSubstitutions []string
+		output               string
+		err                  error
+		entityName           string
+		metadata             map[string]string
+		aliasAccessor        string
+		aliasID              string
+		aliasName            string
+		nilEntity            bool
+		validityCheckOnly    bool
+		aliasMetadata        map[string]string
+		aliasCustomMetadata  map[string]string
+		groupName            string
+		groupMetadata        map[string]string
+		groupMemberships     []string
+		now                  time.Time
 	}{
 		// time.* tests. Keep tests with time.Now() at the front to avoid false
 		// positives due to the second changing during the test
@@ -380,6 +381,56 @@ func TestPopulate_Basic(t *testing.T) {
 			aliasCustomMetadata: map[string]string{"foo": "abc", "bar": "123"},
 			output:              `{}`,
 		},
+
+		// wildcard injection tests
+		{
+			mode:                 ACLTemplating,
+			name:                 "wildcard in template definition (acl)",
+			input:                `path "*" {{identity.entity.metadata.x}}`,
+			blockedSubstitutions: []string{"*", "+"},
+			metadata:             map[string]string{"x": "ok", "unused_wildcard_is_ok": "*"},
+			output:               `path "*" ok`,
+		},
+		{
+			mode:                 ACLTemplating,
+			name:                 "wildcard star in template substitution (acl)",
+			input:                `path "bad" {{identity.entity.metadata.x}}`,
+			blockedSubstitutions: []string{"*", "+"},
+			metadata:             map[string]string{"x": "this * is not ok"},
+			err:                  errors.New(`template substitution contains forbidden value "*"`),
+		},
+		{
+			mode:                 ACLTemplating,
+			name:                 "allowed wildcard in template substitution (acl)",
+			input:                `path "ok" "{{identity.entity.metadata.x}}"`,
+			blockedSubstitutions: []string{},
+			metadata:             map[string]string{"x": "this + is * explicitly allowed"},
+			output:               `path "ok" "this + is * explicitly allowed"`,
+		},
+		{
+			mode:                 JSONTemplating,
+			name:                 "wildcard in template definition (json)",
+			input:                `{ "test/*": {{identity.entity.metadata.x}} }`,
+			blockedSubstitutions: []string{"*", "+"},
+			metadata:             map[string]string{"x": "ok", "unused_wildcard_is_ok": "*"},
+			output:               `{ "test/*": "ok" }`,
+		},
+		{
+			mode:                 JSONTemplating,
+			name:                 "wildcard in template substitution (json)",
+			input:                `{ "test/bad": {{identity.entity.metadata.x}} }`,
+			blockedSubstitutions: []string{},
+			metadata:             map[string]string{"x": "this * is also + ok"},
+			output:               `{ "test/bad": "this * is also + ok" }`,
+		},
+		{
+			mode:                 JSONTemplating,
+			name:                 "explicitly block string in template substitution (json)",
+			input:                `{ "test/bad": {{identity.entity.metadata.x}} }`,
+			blockedSubstitutions: []string{"that", "this", "other"},
+			metadata:             map[string]string{"x": `+ and * are ok, but "this" is not`},
+			err:                  errors.New(`template substitution contains forbidden value "this"`),
+		},
 	}
 
 	for _, test := range tests {
@@ -422,20 +473,21 @@ func TestPopulate_Basic(t *testing.T) {
 		}
 
 		subst, out, err := PopulateString(PopulateStringInput{
-			Mode:              test.mode,
-			ValidityCheckOnly: test.validityCheckOnly,
-			String:            test.input,
-			Entity:            entity,
-			Groups:            groups,
-			NamespaceID:       "root",
-			Now:               test.now,
+			Mode:                 test.mode,
+			ValidityCheckOnly:    test.validityCheckOnly,
+			String:               test.input,
+			BlockedSubstitutions: test.blockedSubstitutions,
+			Entity:               entity,
+			Groups:               groups,
+			NamespaceID:          "root",
+			Now:                  test.now,
 		})
 		if err != nil {
 			if test.err == nil {
 				t.Fatalf("%s: expected success, got error: %v", test.name, err)
 			}
 			if err.Error() != test.err.Error() {
-				t.Fatalf("%s: got error: %v", test.name, err)
+				t.Fatalf("%s: expected %v, got error: %v", test.name, test.err, err)
 			}
 		}
 		if out != test.output {
diff --git a/vault/external_tests/policy/acl_templating_test.go b/vault/external_tests/policy/acl_templating_test.go
index 9faa876b47bf0cd65862646a6a1a1da2ede27715..860854eaffa9a24a680040013945b5573f340b74 100644
--- a/vault/external_tests/policy/acl_templating_test.go
+++ b/vault/external_tests/policy/acl_templating_test.go
@@ -18,12 +18,14 @@ func TestPolicyTemplating(t *testing.T) {
 	goodPolicy1 := `
 path "secret/{{ identity.entity.name}}/*" {
 	capabilities = ["read", "create", "update"]
-
 }
 
 path "secret/{{ identity.entity.aliases.%s.name}}/*" {
 	capabilities = ["read", "create", "update"]
+}
 
+path "secret/{{ identity.entity.metadata.key}}/*" {
+	capabilities = ["read", "create", "update"]
 }
 `
 
@@ -67,6 +69,9 @@ path "secret/{{ identity.groups.names.foobar.name}}/*" {
 			"goodPolicy1",
 			"badPolicy1",
 		},
+		"metadata": map[string]string{
+			"key": "metadata",
+		},
 	})
 	if err != nil {
 		t.Fatal(err)
@@ -180,18 +185,25 @@ path "secret/{{ identity.groups.names.foobar.name}}/*" {
 			name: "bad group name",
 			path: "secret/foobar/foo",
 		},
+		{
+			name: "entity metadata",
+			path: "secret/metadata/test/foo",
+		},
 	}
 
-	runTests := func(failGroupName bool) {
+	runTests := func(failGroupName, failMetadata bool) {
 		for _, test := range tests {
 			resp, err := client.Logical().Write(test.path, map[string]interface{}{"zip": "zap"})
 			fail := test.fail
 			if test.name == "bad group name" {
 				fail = failGroupName
 			}
+			if test.name == "entity metadata" {
+				fail = failMetadata
+			}
 			if err != nil && !fail {
-				if resp.Data["error"].(string) != "permission denied" {
-					t.Fatalf("unexpected status %v", resp.Data["error"])
+				if resp != nil && resp.Data["error"].(string) != "permission denied" {
+					t.Fatalf("%s: unexpected status %v", test.name, resp.Data["error"])
 				}
 				t.Fatalf("%s: got unexpected error: %v", test.name, err)
 			}
@@ -203,7 +215,7 @@ path "secret/{{ identity.groups.names.foobar.name}}/*" {
 
 	rootToken := client.Token()
 	client.SetToken(clientToken)
-	runTests(true)
+	runTests(true, false)
 
 	client.SetToken(rootToken)
 	// Test that a policy with bad group membership doesn't kill the other paths
@@ -212,7 +224,7 @@ path "secret/{{ identity.groups.names.foobar.name}}/*" {
 		t.Fatal(err)
 	}
 	client.SetToken(clientToken)
-	runTests(true)
+	runTests(true, false)
 
 	// Test that adding group membership now allows access
 	client.SetToken(rootToken)
@@ -226,5 +238,34 @@ path "secret/{{ identity.groups.names.foobar.name}}/*" {
 		t.Fatal(err)
 	}
 	client.SetToken(clientToken)
-	runTests(false)
+	runTests(false, false)
+
+	// Test invalid metadata is rejected (wildcard characters and slashes)
+	client.SetToken(rootToken)
+	_, err = client.Logical().WriteWithContext(t.Context(), "identity/entity", map[string]any{
+		"name": "entity_name",
+		"metadata": map[string]string{
+			"key": "metadata/+",
+		},
+	})
+	if err != nil {
+		t.Fatal(err)
+	}
+
+	client.SetToken(clientToken)
+	runTests(false, true)
+
+	// Test with explicitly allowed wildcards and slashes
+	client.SetToken(rootToken)
+	_, err = client.Logical().WriteWithContext(t.Context(), "sys/policy/goodPolicy1", map[string]any{
+		"policy":                           goodPolicy1,
+		"allow_wildcards_in_substitutions": true,
+		"allow_slashes_in_substitutions":   true,
+	})
+	if err != nil {
+		t.Fatal(err)
+	}
+
+	client.SetToken(clientToken)
+	runTests(false, false)
 }
diff --git a/vault/logical_system.go b/vault/logical_system.go
index 5d4e6db6c7060e6962149b84d5f6ff3ea433f9bb..78a0bf609d589a31323f88cf12dfdfa5bec52ba8 100644
--- a/vault/logical_system.go
+++ b/vault/logical_system.go
@@ -2522,10 +2522,12 @@ func (b *SystemBackend) handlePoliciesRead(policyType policy.Type) framework.Ope
 
 func readPolicyResponse(policy *policy.Policy) map[string]interface{} {
 	data := map[string]interface{}{
-		"name":         policy.Name,
-		"version":      policy.DataVersion,
-		"cas_required": policy.CASRequired,
-		"policy":       policy.Raw,
+		"name":                             policy.Name,
+		"version":                          policy.DataVersion,
+		"cas_required":                     policy.CASRequired,
+		"policy":                           policy.Raw,
+		"allow_wildcards_in_substitutions": policy.AllowWildcardsInSubstitutions,
+		"allow_slashes_in_substitutions":   policy.AllowSlashesInSubstitutions,
 	}
 
 	if !policy.Expiration.IsZero() {
@@ -2616,6 +2618,9 @@ func (b *SystemBackend) handlePoliciesSet(policyType policy.Type) framework.Oper
 		casRequired := data.Get("cas_required").(bool)
 		pol.CASRequired = casRequired
 
+		pol.AllowWildcardsInSubstitutions = data.Get("allow_wildcards_in_substitutions").(bool)
+		pol.AllowSlashesInSubstitutions = data.Get("allow_slashes_in_substitutions").(bool)
+
 		// Update the policy
 		if err := b.Core.policyStore.SetPolicy(ctx, pol, cas); err != nil {
 			return handleError(err)
diff --git a/vault/logical_system_paths.go b/vault/logical_system_paths.go
index 3d583d787029013f298ff5b9c27de8055bde06a2..6301c4252a1ea9291398662f7481c909247de06c 100644
--- a/vault/logical_system_paths.go
+++ b/vault/logical_system_paths.go
@@ -3620,6 +3620,14 @@ func (b *SystemBackend) policyPaths() []*framework.Path {
 					Type:        framework.TypeBool,
 					Description: strings.TrimSpace(sysHelp["policy-rules"][0]),
 				},
+				"allow_wildcards_in_substitutions": {
+					Type:    framework.TypeBool,
+					Default: false,
+				},
+				"allow_slashes_in_substitutions": {
+					Type:    framework.TypeBool,
+					Default: false,
+				},
 			},
 
 			Operations: map[logical.Operation]framework.OperationHandler{
@@ -3657,6 +3665,14 @@ func (b *SystemBackend) policyPaths() []*framework.Path {
 									Type:     framework.TypeBool,
 									Required: true,
 								},
+								"allow_wildcards_in_substitutions": {
+									Type:     framework.TypeBool,
+									Required: true,
+								},
+								"allow_slashes_in_substitutions": {
+									Type:     framework.TypeBool,
+									Required: true,
+								},
 							},
 						}},
 					},
@@ -3770,6 +3786,14 @@ func (b *SystemBackend) policyPaths() []*framework.Path {
 					Type:        framework.TypeBool,
 					Description: strings.TrimSpace(sysHelp["policy-rules"][0]),
 				},
+				"allow_wildcards_in_substitutions": {
+					Type:    framework.TypeBool,
+					Default: false,
+				},
+				"allow_slashes_in_substitutions": {
+					Type:    framework.TypeBool,
+					Default: false,
+				},
 			},
 
 			Operations: map[logical.Operation]framework.OperationHandler{
@@ -3807,6 +3831,14 @@ func (b *SystemBackend) policyPaths() []*framework.Path {
 									Type:     framework.TypeBool,
 									Required: true,
 								},
+								"allow_wildcards_in_substitutions": {
+									Type:     framework.TypeBool,
+									Required: true,
+								},
+								"allow_slashes_in_substitutions": {
+									Type:     framework.TypeBool,
+									Required: true,
+								},
 							},
 						}},
 					},
diff --git a/vault/logical_system_test.go b/vault/logical_system_test.go
index 53726c429ec50fb4b2989fb84849337b06bfd3f6..f7179bf595dea36260727266e452bca102659deb 100644
--- a/vault/logical_system_test.go
+++ b/vault/logical_system_test.go
@@ -2479,10 +2479,12 @@ func TestSystemBackend_policyCRUD(t *testing.T) {
 	delete(resp.Data, "modified")
 
 	exp := map[string]interface{}{
-		"name":         "foo",
-		"rules":        rules,
-		"cas_required": false,
-		"version":      1,
+		"name":                             "foo",
+		"rules":                            rules,
+		"cas_required":                     false,
+		"version":                          1,
+		"allow_slashes_in_substitutions":   false,
+		"allow_wildcards_in_substitutions": false,
 	}
 	if !reflect.DeepEqual(resp.Data, exp) {
 		t.Fatalf("got: %#v expect: %#v", resp.Data, exp)
@@ -2501,10 +2503,12 @@ func TestSystemBackend_policyCRUD(t *testing.T) {
 	delete(resp.Data, "modified")
 
 	exp = map[string]interface{}{
-		"name":         "foo",
-		"rules":        rules,
-		"cas_required": false,
-		"version":      1,
+		"name":                             "foo",
+		"rules":                            rules,
+		"cas_required":                     false,
+		"version":                          1,
+		"allow_slashes_in_substitutions":   false,
+		"allow_wildcards_in_substitutions": false,
 	}
 	if !reflect.DeepEqual(resp.Data, exp) {
 		t.Fatalf("got: %#v expect: %#v", resp.Data, exp)
diff --git a/vault/policy/policy.go b/vault/policy/policy.go
index 2f22fd45265ae094d3bead2de960a6323af61559..2615e4f4c81a2e4d023e7dd80a77a672b56b5190 100644
--- a/vault/policy/policy.go
+++ b/vault/policy/policy.go
@@ -94,30 +94,34 @@ var cap2Int = map[string]uint32{
 
 // Policy is used to represent the policy specified by an ACL configuration.
 type Policy struct {
-	Name        string `hcl:"name"`
-	DataVersion int
-	CASRequired bool
-	Paths       []*PathRules `hcl:"-"`
-	Raw         string
-	Type        Type
-	Templated   bool
-	Expiration  time.Time
-	Modified    time.Time
-	Namespace   *namespace.Namespace
+	Name                          string `hcl:"name"`
+	DataVersion                   int
+	CASRequired                   bool
+	Paths                         []*PathRules `hcl:"-"`
+	Raw                           string
+	Type                          Type
+	Templated                     bool
+	Expiration                    time.Time
+	Modified                      time.Time
+	Namespace                     *namespace.Namespace
+	AllowWildcardsInSubstitutions bool
+	AllowSlashesInSubstitutions   bool
 }
 
 // ShallowClone returns a shallow clone of the policy. This should not be used
 // if any of the reference-typed fields are going to be modified
 func (p *Policy) ShallowClone() *Policy {
 	return &Policy{
-		Name:        p.Name,
-		DataVersion: p.DataVersion,
-		CASRequired: p.CASRequired,
-		Paths:       p.Paths,
-		Raw:         p.Raw,
-		Type:        p.Type,
-		Templated:   p.Templated,
-		Namespace:   p.Namespace,
+		Name:                          p.Name,
+		DataVersion:                   p.DataVersion,
+		CASRequired:                   p.CASRequired,
+		Paths:                         p.Paths,
+		Raw:                           p.Raw,
+		Type:                          p.Type,
+		Templated:                     p.Templated,
+		Namespace:                     p.Namespace,
+		AllowWildcardsInSubstitutions: p.AllowWildcardsInSubstitutions,
+		AllowSlashesInSubstitutions:   p.AllowSlashesInSubstitutions,
 	}
 }
 
@@ -291,14 +295,14 @@ func addGrantingPoliciesToMap(m map[uint32][]logical.PolicyInfo, policy *Policy,
 // intermediary set of policies, before being compiled into
 // the ACL
 func ParseACLPolicy(ns *namespace.Namespace, rules string) (*Policy, error) {
-	return ParseACLPolicyWithTemplating(ns, rules, false, nil, nil)
+	return ParseACLPolicyWithTemplating(ns, rules, false, nil, nil, nil)
 }
 
 // ParseACLPolicyWithTemplating performs the actual work and checks whether we
 // should perform substitutions. If performTemplating is true we know that it
 // is templated so we don't check again, otherwise we check to see if it's a
 // templated policy.
-func ParseACLPolicyWithTemplating(ns *namespace.Namespace, rules string, performTemplating bool, entity *identity.Entity, groups []*identity.Group) (*Policy, error) {
+func ParseACLPolicyWithTemplating(ns *namespace.Namespace, rules string, performTemplating bool, blockedSubstitutions []string, entity *identity.Entity, groups []*identity.Group) (*Policy, error) {
 	// Parse the rules
 	root, err := hclutil.ParseConfig([]byte(rules))
 	if err != nil {
@@ -331,7 +335,7 @@ func ParseACLPolicyWithTemplating(ns *namespace.Namespace, rules string, perform
 	}
 
 	if o := list.Filter("path"); len(o.Items) > 0 {
-		if err := parsePaths(&p, o, performTemplating, entity, groups); err != nil {
+		if err := parsePaths(&p, o, performTemplating, blockedSubstitutions, entity, groups); err != nil {
 			return nil, fmt.Errorf("failed to parse policy: %w", err)
 		}
 	}
@@ -339,7 +343,7 @@ func ParseACLPolicyWithTemplating(ns *namespace.Namespace, rules string, perform
 	return &p, nil
 }
 
-func parsePaths(result *Policy, list *ast.ObjectList, performTemplating bool, entity *identity.Entity, groups []*identity.Group) error {
+func parsePaths(result *Policy, list *ast.ObjectList, performTemplating bool, blockedSubstitutions []string, entity *identity.Entity, groups []*identity.Group) error {
 	paths := make([]*PathRules, 0, len(list.Items))
 	for _, item := range list.Items {
 		key := "path"
@@ -350,11 +354,12 @@ func parsePaths(result *Policy, list *ast.ObjectList, performTemplating bool, en
 		// Check the path
 		if performTemplating {
 			_, templated, err := identitytpl.PopulateString(identitytpl.PopulateStringInput{
-				Mode:        identitytpl.ACLTemplating,
-				String:      key,
-				Entity:      identity.ToSDKEntity(entity),
-				Groups:      identity.ToSDKGroups(groups),
-				NamespaceID: result.Namespace.ID,
+				Mode:                 identitytpl.ACLTemplating,
+				String:               key,
+				Entity:               identity.ToSDKEntity(entity),
+				Groups:               identity.ToSDKGroups(groups),
+				NamespaceID:          result.Namespace.ID,
+				BlockedSubstitutions: blockedSubstitutions,
 			})
 			if err != nil {
 				continue
diff --git a/vault/policy/policy_store.go b/vault/policy/policy_store.go
index 600cee16cd2ea22f407697e3646b624d48bcc1a0..be23db8cb7670c543019ffea6a1876c2c339c7a5 100644
--- a/vault/policy/policy_store.go
+++ b/vault/policy/policy_store.go
@@ -676,7 +676,16 @@ func (ps *Store) ACL(ctx context.Context, entity *identity.Entity, policyNames m
 					groups = append(directGroups, inheritedGroups...)
 				}
 			}
-			p, err := ParseACLPolicyWithTemplating(pol.Namespace, pol.Raw, true, entity, groups)
+
+			blockedSubstitutions := make([]string, 0, 3)
+			if !pol.AllowSlashesInSubstitutions {
+				blockedSubstitutions = append(blockedSubstitutions, "/")
+			}
+			if !pol.AllowWildcardsInSubstitutions {
+				blockedSubstitutions = append(blockedSubstitutions, "*", "+")
+			}
+
+			p, err := ParseACLPolicyWithTemplating(pol.Namespace, pol.Raw, true, blockedSubstitutions, entity, groups)
 			if err != nil {
 				return nil, fmt.Errorf("error parsing templated policy %q: %w", pol.Name, err)
 			}
diff --git a/website/content/api-docs/secret/pki.mdx b/website/content/api-docs/secret/pki.mdx
index 5adea24f67fd6b6e0eb13a5cf97837ec1480a020..0bfe3a8780556bbd9ffdd739c539dcb471aebd59 100644
--- a/website/content/api-docs/secret/pki.mdx
+++ b/website/content/api-docs/secret/pki.mdx
@@ -551,6 +551,7 @@ $ curl \
 {
   "data": {
     "allow_any_name": false,
+    "allow_globs_in_substitutions": false,
     "allow_ip_sans": true,
     "allow_localhost": true,
     "allow_subdomains": false,
@@ -3733,6 +3734,12 @@ allowing update of specific fields. Note that `bao write` uses `POST`.
   forbidden. It is strongly recommended to allow OpenBao to generate random
   serial numbers instead.
 
+- `allow_globs_in_substitutions` `(bool: false)` - If set and templating is
+  enabled, the values substituted in for `allowed_uri_sans_template` and
+  `allowed_domains` template expression might contain a glob characters ('*').
+  This can enable injection attacks. Only use this, if the data used by the
+  templates is trusted. Defaults to false.
+
 - `server_flag` `(bool: true)` - Specifies if certificates are flagged for
   server authentication use. See [RFC 5280 Section 4.2.1.12](https://datatracker.ietf.org/doc/html/rfc5280#section-4.2.1.12)
   for information about the Extended Key Usage field.
diff --git a/website/content/api-docs/secret/ssh.mdx b/website/content/api-docs/secret/ssh.mdx
index 06af29416758e59e957ae95e3718006246a02103..4123035546a72afd62033650a01962a4dbe25fca 100644
--- a/website/content/api-docs/secret/ssh.mdx
+++ b/website/content/api-docs/secret/ssh.mdx
@@ -363,6 +363,12 @@ to `*` (corresponding to the role/certificate type),
   use for signing requests. If not set, the default issuer will be used.
   This field is only applicable for CA type roles.
 
+- `allow_commas_in_substitutions` `(bool: false)` - If set and templating
+  is enabled, the values substituted in for `allowed_users` and
+  `allowed_domains` template expressions might contain a comma (','). As these
+  values are comma separated lists, this can enable injection attacks. Only use
+  this, if the data used by the templates is trusted. Defaults to false.
+
 #### Sample payload
 
 ```json
@@ -424,6 +430,7 @@ For a CA role:
   "allow_subdomains": false,
   "allow_user_key_ids": false,
   "allow_user_certificates": true,
+  "allow_commas_in_substitutions": false,
   "allowed_critical_options": "",
   "allowed_extensions": "",
   "default_critical_options": {},
diff --git a/website/content/api-docs/system/policy.mdx b/website/content/api-docs/system/policy.mdx
index ece0467fbc0b47a0d6a973517dd51f02fd50d342..2c630d84e18a4aea970da01e03b72ab73164c2d5 100644
--- a/website/content/api-docs/system/policy.mdx
+++ b/website/content/api-docs/system/policy.mdx
@@ -61,7 +61,9 @@ $ curl \
   "rules": "path \"secret/*\"...",
   "modified": "2025-03-25T16:50:49.348095648-05:00",
   "version": "1",
-  "cas_required": false
+  "cas_required": false,
+  "allow_slashes_in_substitutions": false,
+  "allow_wildcards_in_substitutions": false
 }
 ```
 
@@ -103,6 +105,17 @@ updated, it takes effect immediately to all associated users.
   subsequent operation for continued usage. When set to true, `cas` becomes
   a required parameter. Defaults to false.
 
+- `allow_slashes_in_substitutions` `(bool: <optional>)` - If set, the values
+  substituted in for template expression in the policy definition might contain
+  a slash ('/'). This can enable injection attacks. Only use this, if the data
+  used by the templates is trusted. Defaults to false.
+
+- `allow_wildcards_in_substitutions` `(bool: <optional>)` - If set, the values
+  substituted in for template expression in the policy definition might contain
+  a wildcard characters ('*' and '+'). This can enable injection attacks. Only
+  use this, if the data used by the templates is trusted. Defaults to false.
+
+
 ### Sample payload
 
 ```json

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### builtin/logical/pki/cert_util.go
```
// Copyright (c) HashiCorp, Inc.
// SPDX-License-Identifier: MPL-2.0

package pki

import (
	"crypto"
	"crypto/ecdsa"
	"crypto/ed25519"
	"crypto/rsa"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/asn1"
	"encoding/base64"
	"encoding/hex"
	"encoding/pem"
	"errors"
	"fmt"
	"io"
	"math/big"
	"net"
	"net/url"
	"regexp"
	"slices"
	"strconv"
	"strings"
	"time"

	"github.com/hashicorp/go-secure-stdlib/strutil"
	"github.com/openbao/openbao/sdk/v2/framework"
	"github.com/openbao/openbao/sdk/v2/helper/certutil"
	"github.com/openbao/openbao/sdk/v2/helper/errutil"
	"github.com/openbao/openbao/sdk/v2/logical"
	"github.com/ryanuber/go-glob"
	"golang.org/x/crypto/cryptobyte"
	cbbasn1 "golang.org/x/crypto/cryptobyte/asn1"
	"golang.org/x/net/idna"
)

type inputBundle struct {
	role    *roleEntry
	req     *logical.Request
	apiData *framework.FieldData
}

var (
	// labelRegex is a single label from a valid domain name and was extracted
	// from hostnameRegex below for use in leftWildLabelRegex, without any
	// label separators (`.`).
	labelRegex = `([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])`

	// A note on hostnameRegex: although we set the StrictDomainName option
	// when doing the idna conversion, this appears to only affect output, not
	// input, so it will allow e.g. host^123.example.com straight through. So
	// we still need to use this to check the output.
	hostnameRegex = regexp.MustCompile(`^(\*\.)?(` + labelRegex + `\.)*` + labelRegex + `\.?$`)

	// Left Wildcard Label Regex is equivalent to a single domain label
	// component from hostnameRegex above, but with additional wildcard
	// characters added. There are four possibilities here:
	//
	//  1. Entire label is a wildcard,
	//  2. Wildcard exists at the start,
	//  3. Wildcard exists at the end,
	//  4. Wildcard exists in the middle.
	allWildRegex       = `\*`
	startWildRegex     = `\*` + labelRegex
	endWildRegex       = labelRegex + `\*`
	middleWildRegex    = labelRegex + `\*` + labelRegex
	leftWildLabelRegex = regexp.MustCompile(`^(` + allWildRegex + `|` + startWildRegex + `|` + endWildRegex + `|` + middleWildRegex + `)$`)

	// OIDs for X.509 certificate extensions used below.
	oidExtensionSubjectAltName = []int{2, 5, 29, 17}
)

func getFormat(data *framework.FieldData) string {
	format := data.Get("format").(string)
	switch format {
	case "pem":
	case "der":
	case "pem_bundle":
	default:
		format = ""
	}
	return format
}

// fetchCAInfo will fetch the CA info, will return an error if no ca info exists, this does NOT support
// loading using the legacyBundleShimID and should be used with care. This should be called only once
// within the request path otherwise you run the risk of a race condition with the issuer migration on perf-secondaries.
func (sc *storageContext) fetchCAInfo(issuerRef string, usage issuerUsage) (*certutil.CAInfoBundle, error) {
	bundle, _, err := sc.fetchCAInfoWithIssuer(issuerRef, usage)
	return bundle, err
}

func (sc *storageContext) fetchCAInfoWithIssuer(issuerRef string, usage issuerUsage) (*certutil.CAInfoBundle, issuerID, error) {
	var issuerId issuerID

	if sc.Backend.useLegacyBundleCaStorage() {
		// We have not completed the migration so attempt to load the bundle from the legacy location
		sc.Backend.Logger().Info("Using legacy CA bundle as PKI migration has not completed.")
		issuerId = legacyBundleShimID
	} else {
		var err error
		issuerId, err = sc.resolveIssuerReference(issuerRef)
		if err != nil {
			// Usually a bad label from the user or mis-configured default.
			return nil, IssuerRefNotFound, errutil.UserError{Err: err.Error()}
		}
	}

	bundle, err := sc.fetchCAInfoByIssuerId(issuerId, usage)
	if err != nil {
		return nil, IssuerRefNotFound, err
	}

	return bundle, issuerId, nil
}

// fetchCAInfoByIssuerId will fetch the CA info, will return an error if no ca info exists for the given issuerId.
// This does support the loading using the legacyBundleShimID
func (sc *storageContext) fetchCAInfoByIssuerId(issuerId issuerID, usage issuerUsage) (*certutil.CAInfoBundle, error) {
	entry, bundle, err := sc.fetchCertBundleByIssuerId(issuerId, true)
	if err != nil {
		switch err.(type) {
		case errutil.UserError:
			return nil, err
		case errutil.InternalError:
			return nil, err
		default:
			return nil, errutil.InternalError{Err: fmt.Sprintf("error fetching CA info: %v", err)}
		}
	}

	if err := entry.EnsureUsage(usage); err != nil {
		return nil, errutil.InternalError{Err: fmt.Sprintf("error while attempting to use issuer %v: %v", issuerId, err)}
	}

	parsedBundle, err := bundle.ToParsedCertBundle()
	if err != nil {
		return nil, errutil.InternalError{Err: err.Error()}
	}

	if parsedBundle.Certificate == nil {
		return nil, errutil.InternalError{Err: "stored CA information not able to be parsed"}
	}
	if parsedBundle.PrivateKey == nil {
		return nil, errutil.UserError{Err: fmt.Sprintf("unable to fetch corresponding key for issuer %v; unable to use this issuer for signing", issuerId)}
	}

	caInfo := &certutil.CAInfoBundle{
		ParsedCertBundle:     *parsedBundle,
		URLs:                 nil,
		LeafNotAfterBehavior: entry.LeafNotAfterBehavior,
		RevocationSigAlg:     entry.RevocationSigAlg,
	}

	entries, err := entry.GetAIAURLs(sc)
	if err != nil {
		return nil, errutil.InternalError{Err: fmt.Sprintf("unable to fetch AIA URL information: %v", err)}
	}
	caInfo.URLs = entries

	return caInfo, nil
}

func fetchCertBySerialBigInt(sc *storageContext, prefix string, serial *big.Int) (*logical.StorageEntry, error) {
	return fetchCertBySerial(sc, prefix, serialFromBigInt(serial))
}

// Allows fetching certificates from the backend; it handles the slightly
// separate pathing for CRL, and revoked certificates.
//
// Support for fetching CA certificates was removed, due to the new issuers
// changes.
func fetchCertBySerial(sc *storageContext, prefix, serial string) (*logical.StorageEntry, error) {
	var path, legacyPath string
	var err error
	var certEntry *logical.StorageEntry

	hyphenSerial := normalizeSerial(serial)
	colonSerial := strings.ReplaceAll(strings.ToLower(serial), "-", ":")

	switch {
	// Revoked goes first as otherwise crl get hardcoded paths which fail if
	// we actually want revocation info
	case strings.HasPrefix(prefix, "revoked/"):
		legacyPath = "revoked/" + colonSerial
		path = "revoked/" + hyphenSerial
	case serial == legacyCRLPath || serial == deltaCRLPath:
		warnings, err := sc.Backend.crlBuilder.rebuildIfForced(sc)
		if err != nil {
			return nil, err
		}
		if len(warnings) > 0 {
			msg := "During rebuild of CRL for cert fetch, got the following warnings:"
			for index, warning := range warnings {
				msg = fmt.Sprintf("%v\n %d. %v", msg, index+1, warning)
			}
			sc.Backend.Logger().Warn(msg)
		}

		path, err = sc.resolveIssuerCRLPath(defaultRef)
		if err != nil {
			return nil, err
		}

		if serial == deltaCRLPath {
			if sc.Backend.useLegacyBundleCaStorage() {
				return nil, errors.New("refusing to serve delta CRL with legacy CA bundle")
			}

			path += deltaCRLPathSuffix
		}
	default:
		legacyPath = "certs/" + colonSerial
		path = "certs/" + hyphenSerial
	}

	certEntry, err = sc.Storage.Get(sc.Context, path)
	if err != nil {
		return nil, errutil.InternalError{Err: fmt.Sprintf("error fetching certificate %s: %s", serial, err)}
	}
	if certEntry != nil {
		if len(certEntry.Value) == 0 {
			return nil, errutil.InternalError{Err: fmt.Sprintf("returned certificate bytes for serial %s were empty", serial)}
		}
		return certEntry, nil
	}

	// If legacyPath is unset, it's going to be a CA or CRL; return immediately
	if legacyPath == "" {
		return nil, nil
	}

	// Retrieve the old-style path.  We disregard errors here because they
	// always manifest on Windows, and thus the initial check for a revoked
	// cert fails would return an error when the cert isn't revoked, preventing
	// the happy path from working.
	certEntry, _ = sc.Storage.Get(sc.Context, legacyPath)
	if certEntry == nil {
		return nil, nil
	}
	if len(certEntry.Value) == 0 {
		return nil, errutil.InternalError{Err: fmt.Sprintf("returned certificate bytes for serial %s were empty", serial)}
	}

	// Update old-style paths to new-style paths
	certEntry.Key = path
	certsCounted := sc.Backend.certsCounted.Load()
	if err = sc.Storage.Put(sc.Context, certEntry); err != nil {
		return nil, errutil.InternalError{Err: fmt.Sprintf("error saving certificate with serial %s to new location", serial)}
	}
	if err = sc.Storage.Delete(sc.Context, legacyPath); err != nil {
		// If we fail here, we have an extra (copy) of a cert in storage, add to metrics:
		switch {
		case strings.HasPrefix(prefix, "revoked/"):
			sc.Backend.ifCountEnabledIncrementTotalRevokedCertificatesCount(certsCounted, path)
		default:
			sc.Backend.ifCountEnabledIncrementTotalCertificatesCount(certsCounted, path)
		}
		return nil, errutil.InternalError{Err: fmt.Sprintf("error deleting certificate with serial %s from old location", serial)}
	}

	return certEntry, nil
}

// Given a URI SAN, verify that it is allowed.
func validateURISAN(b *backend, data *inputBundle, uri string) bool {
	valid := false
	for _, allowed := range data.role.AllowedURISANs {
		if data.role.AllowedURISANsTemplate {
			isTemplate, _ := framework.ValidateIdentityTemplate(allowed)
			if isTemplate && data.req.EntityID != "" {
				tmpAllowed, err := framework.PopulateIdentityTemplate(allowed, data.req.EntityID, b.System())
				if err != nil {
					continue
				}
				allowed = tmpAllowed
			}
		}
		validURI := glob.Glob(allowed, uri)
		if validURI {
			valid = true
			break
		}
	}
	return valid
}

// Validates a given common name, ensuring it's either an email or a hostname
// after validating it according to the role parameters, or disables
// validation altogether.
func validateCommonName(b *backend, data *inputBundle, name string) string {
	isDisabled := len(data.role.CNValidations) == 1 && data.role.CNValidations[0] == "disabled"
	if isDisabled {
		return ""
	}

	if validateNames(b, data, []string{name}) != "" {
		return name
	}

	// Validations weren't disabled, but the role lacked CN Validations, so
	// don't restrict types. This case is hit in certain existing tests.
	if len(data.role.CNValidations) == 0 {
		return ""
	}

	// If there's an at in the data, ensure email type validation is allowed.
	// Otherwise, ensure hostname is allowed.
	if strings.Contains(name, "@") {
		if !slices.Contains(data.role.CNValidations, "email") {
			return name
		}
	} else {
		if !slices.Contains(data.role.CNValidations, "hostname") {
			return name
		}
	}

	return ""
}

func isWildcardDomain(name string) bool {
	// Per RFC 6125 Section 6.4.3, and explicitly contradicting the earlier
	// RFC 2818 which no modern client will validate against, there are two
	// main types of wildcards, each with a single wildcard specifier (`*`,
	// functionally different from the `*` used as a glob from the
	// AllowGlobDomains parsing path) in the left-most label:
	//
	//  1. Entire label is a single wildcard character (most common and
	//     well-supported),
	//  2. Part of the label contains a single wildcard character (e.g. per
	//     RFC 6125: baz*.example.net, *baz.example.net, or b*z.example.net).
	//
	// We permit issuance of both but not the older RFC 2818 style under
	// the new AllowWildcardCertificates option. However, anything with a
	// glob character is technically a wildcard, though not a valid one.

	return strings.Contains(name, "*")
}

func validateWildcardDomain(name string) (string, string, error) {
	// See note in isWildcardDomain(...) about the definition of a wildcard
	// domain.
	var wildcardLabel string
	var reducedName string

	if strings.Count(name, "*") > 1 {
		// As mentioned above, only one wildcard character is permitted
		// under RFC 6125 semantics.
		return wildcardLabel, reducedName, errors.New("expected only one wildcard identifier in the given domain name")
	}

	// Split the Common Name into two parts: a left-most label and the
	// remaining segments (if present).
	splitLabels := strings.SplitN(name, ".", 2)
	if len(splitLabels) != 2 {
		// We've been given a single-part domain name that consists
		// entirely of a wildcard. This is a little tricky to handle,
		// but EnforceHostnames validates both the wildcard-containing
		// label and the reduced name, but _only_ the latter if it is
		// non-empty. This allows us to still validate the only label
		// component matches hostname expectations still.
		wildcardLabel = splitLabels[0]
		reducedName = ""
	} else {
		// We have a (at least) two label domain name. But before we can
		// update our names, we need to validate the wildcard ended up
		// in the segment we expected it to. While this is (kinda)
		// validated under EnforceHostnames's leftWildLabelRegex, we
		// still need to validate it in the non-enforced mode.
		//
		// By validated assumption above, we know there's strictly one
		// wildcard in this domain so we only need to check the wildcard
		// label or the reduced name (as one is equivalent to the other).
		// Because we later assume reducedName _lacks_ wildcard segments,
		// we validate that.
		wildcardLabel = splitLabels[0]
		reducedName = splitLabels[1]
		if strings.Contains(reducedName, "*") {
			return wildcardLabel, reducedName, errors.New("expected wildcard to only be present in left-most domain label")
		}
	}

	return wildcardLabel, reducedName, nil
}

// Given a set of requested names for a certificate, verifies that all of them
// match the various toggles set in the role for controlling issuance.
// If one does not pass, it is returned in the string argument.
func validateNames(b *backend, data *inputBundle, names []string) string {
	for _, name := range names {
		// Previously, reducedName was called sanitizedName but this made
		// little sense under the previous interpretation of wildcards,
		// leading to two bugs in this implementation. We presently call it
		// "reduced" to indicate that it is still untrusted input (potentially
		// different from the bare Common Name entry we're validating), it
		// might have been modified such as by the removal of wildcard labels
		// or the email prefix.
		reducedName := name
		emailDomain := reducedName
		wildcardLabel := ""
		isEmail := false
		isWildcard := false

		// If it has an @, assume it is an email address and separate out the
		// user from the hostname portion so that we can act on the hostname.
		// Note that this matches behavior from the alt_names parameter. If it
		// ends up being problematic for users, I guess that could be separated
		// into dns_names and email_names in the future to be explicit, but I
		// don't think this is likely.
		if strings.Contains(reducedName, "@") {
			splitEmail := strings.Split(reducedName, "@")
			if len(splitEmail) != 2 {
				return name
			}
			reducedName = splitEmail[1]
			emailDomain = splitEmail[1]
			isEmail = true
		}

		if isWildcardDomain(reducedName) {
			// Regardless of later rejections below, this common name contains
			// a wildcard character and is thus technically a wildcard name.
			isWildcard = true

			// Additionally, if AllowWildcardCertificates is explicitly
			// forbidden, it takes precedence over AllowAnyName, thus we should
			// reject the name now.
			//
			// We expect the role to have been correctly migrated but guard for
			// safety.
			if data.role.AllowWildcardCertificates != nil && !*data.role.AllowWildcardCertificates {
				return name
			}

			// Check that this domain is well-formatted per RFC 6125.
			var err error
			wildcardLabel, reducedName, err = validateWildcardDomain(reducedName)
			if err != nil {
				return name
			}
		}

		// Email addresses using wildcard domain names do not make sense
		// in a Common Name field.
		if isEmail && isWildcard {
			return name
		}

		// AllowAnyName is checked after this because EnforceHostnames still
		// applies when allowing any name. Also, we check the reduced name to
		// ensure that we are not either checking a full email address or a
		// wildcard prefix.
		if data.role.EnforceHostnames {
			if reducedName != "" {
				// See note above about splitLabels having only one segment
				// and setting reducedName to the empty string.
				p := idna.New(
					idna.StrictDomainName(true),
					idna.VerifyDNSLength(true),
				)
				converted, err := p.ToASCII(reducedName)
				if err != nil {
					return name
				}
				if !hostnameRegex.MatchString(converted) {
					return name
				}
			}

			// When a wildcard is specified, we additionally need to validate
			// the label with the wildcard is correctly formed.
			if isWildcard && !leftWildLabelRegex.MatchString(wildcardLabel) {
				return name
			}
		}

		// Self-explanatory, but validations from EnforceHostnames and
		// AllowWildcardCertificates take precedence.
		if data.role.AllowAnyName {
			continue
		}

		// The following blocks all work the same basic way:
		// 1) If a role allows a certain class of base (localhost, token
		// display name, role-configured domains), perform further tests
		//
		// 2) If there is a perfect match on either the sanitized name or it's an
		// email address with a perfect match on the hostname portion, allow it
		//
		// 3) If subdomains are allowed, we check based on the sanitized name;
		// note that if not a wildcard, will be equivalent to the email domain
		// for email checks, and we already checked above for both a wildcard
		// and email address being present in the same name
		// 3a) First we check for a non-wildcard subdomain, as in <name>.<base>
		// 3b) Then we check if it's a wildcard and the base domain is a match
		//
		// Variances are noted in-line

		if data.role.AllowLocalhost {
			if reducedName == "localhost" ||
				reducedName == "localdomain" ||
				(isEmail && emailDomain == "localhost") ||
				(isEmail && emailDomain == "localdomain") {
				continue
			}

			if data.role.AllowSubdomains {
				// It is possible, if unlikely, to have a subdomain of "localhost"
				if strings.HasSuffix(reducedName, ".localhost") ||
					(isWildcard && reducedName == "localhost") {
					continue
				}

				// A subdomain of "localdomain" is also not entirely uncommon
				if strings.HasSuffix(reducedName, ".localdomain") ||
					(isWildcard && reducedName == "localdomain") {
					continue
				}
			}
		}

		if data.role.AllowTokenDisplayName {
			if name == data.req.DisplayName {
				continue
			}

			if data.role.AllowSubdomains {
				if isEmail {
					// If it's an email address, we need to parse the token
					// display name in order to do a proper comparison of the
					// subdomain
					if strings.Contains(data.req.DisplayName, "@") {
						splitDisplay := strings.Split(data.req.DisplayName, "@")
						if len(splitDisplay) == 2 {
							// Compare the sanitized name against the hostname
							// portion of the email address in the broken
							// display name
							if strings.HasSuffix(reducedName, "."+splitDisplay[1]) {
								continue
							}
						}
					}
				}

				if strings.HasSuffix(reducedName, "."+data.req.DisplayName) ||
					(isWildcard && reducedName == data.req.DisplayName) {
					continue
				}
			}
		}

		if len(data.role.AllowedDomains) > 0 {
			valid := false
			for _, currDomain := range data.role.AllowedDomains {
				// If there is, say, a trailing comma, ignore it
				if currDomain == "" {
					continue
				}

				if data.role.AllowedDomainsTemplate {
					isTemplate, _ := framework.ValidateIdentityTemplate(currDomain)
					if isTemplate && data.req.EntityID != "" {
						tmpCurrDomain, err := framework.PopulateIdentityTemplate(currDomain, data.req.EntityID, b.System())
						if err != nil {
							continue
						}

						currDomain = tmpCurrDomain
					}
				}

				// First, allow an exact match of the base domain if that role flag
				// is enabled
				if data.role.AllowBareDomains &&
					(strings.EqualFold(name, currDomain) ||
						(isEmail && strings.EqualFold(emailDomain, currDomain))) {
					valid = true
					break
				}

				if data.role.AllowSubdomains {
					if strings.HasSuffix(reducedName, "."+currDomain) ||
						(isWildcard && strings.EqualFold(reducedName, currDomain)) {
						valid = true
						break
					}
				}

				if data.role.AllowGlobDomains &&
					strings.Contains(currDomain, "*") &&
					glob.Glob(currDomain, name) {
					valid = true
					break
				}
			}

			if valid {
				continue
			}
		}

		return name
	}

	return ""
}

// validateOtherSANs checks if the values requested are allowed. If an OID
// isn't allowed, it will be returned as the first string. If a value isn't
// allowed, it will be returned as the second string. Empty strings + error
// means everything is okay.
func validateOtherSANs(data *inputBundle, requested map[string][]string) (string, string, error) {
	if len(data.role.AllowedOtherSANs) == 1 && data.role.AllowedOtherSANs[0] == "*" {
		// Anything is allowed
		return "", "", nil
	}

	allowed, err := parseOtherSANs(data.role.AllowedOtherSANs)
	if err != nil {
		return "", "", fmt.Errorf("error parsing role's allowed SANs: %w", err)
	}
	for oid, names := range requested {
		for _, name := range names {
			allowedNames, ok := allowed[oid]
			if !ok {
				return oid, "", nil
			}

			valid := false
			for _, allowedName := range allowedNames {
				if glob.Glob(allowedName, name) {
					valid = true
					break
				}
			}

			if !valid {
				return oid, name, nil
			}
		}
	}

	return "", "", nil
}

func parseOtherSANs(others []string) (map[string][]string, error) {
	result := map[string][]string{}
	for _, other := range others {
		splitOther := strings.SplitN(other, ";", 2)
		if len(splitOther) != 2 {
			return nil, fmt.Errorf("expected a semicolon in other SAN %q", other)
		}
		splitType := strings.SplitN(splitOther[1], ":", 2)
		if len(splitType) != 2 {
			return nil, fmt.Errorf("expected a colon in other SAN %q", other)
		}
		switch {
		case strings.EqualFold(splitType[0], "utf8"):
		case strings.EqualFold(splitType[0], "utf-8"):
		default:
			return nil, fmt.Errorf("only utf8 other SANs are supported; found non-supported type in other SAN %q", other)
		}
		result[splitOther[0]] = append(result[splitOther[0]], splitType[1])
	}

	return result, nil
}

// Returns bool stating whether the given UserId is Valid
func validateUserId(data *inputBundle, userId string) bool {
	allowedList := data.role.AllowedUserIDs

	if len(allowedList) == 0 {
		// Nothing is allowed.
		return false
	}

	if strutil.StrListContainsCaseInsensitive(allowedList, userId) {
		return true
	}

	for _, rolePattern := range allowedList {
		if rolePattern == "" {
			continue
		}

		if strings.Contains(rolePattern, "*") && glob.Glob(rolePattern, userId) {
			return true
		}
	}

	// No matches.
	return false
}

func validateSerialNumber(data *inputBundle, serialNumber string) string {
	valid := false
	if len(data.role.AllowedSerialNumbers) > 0 {
		for _, currSerialNumber := range data.role.AllowedSerialNumbers {
			if currSerialNumber == "" {
				continue
			}

			if (strings.Contains(currSerialNumber, "*") &&
				glob.Glob(currSerialNumber, serialNumber)) ||
				currSerialNumber == serialNumber {
				valid = true
				break
			}
		}
	}
	if !valid {
		return serialNumber
	} else {
		return ""
	}
}

func generateCert(sc *storageContext,
	input *inputBundle,
	caSign *certutil.CAInfoBundle,
	isCA bool,
	randomSource io.Reader) (*certutil.ParsedCertBundle, []string, error,
) {
	ctx := sc.Context
	b := sc.Backend

	if input.role == nil {
		return nil, nil, errutil.InternalError{Err: "no role found in data bundle"}
	}

	if input.role.KeyType == "rsa" && input.role.KeyBits < 2048 {
		return nil, nil, errutil.UserError{Err: "RSA keys < 2048 bits are unsafe and not supported"}
	}

	data, warnings, err := generateCreationBundle(b, input, caSign, nil)
	if err != nil {
		return nil, nil, err
	}
	if data.Params == nil {
		return nil, nil, errutil.InternalError{Err: "nil parameters received from parameter bundle generation"}
	}

	if isCA {
		data.Params.IsCA = isCA
		data.Params.PermittedDNSDomains = input.apiData.Get("permitted_dns_domains").([]string)

		if rawKeyUsageValue, ok := input.apiData.GetOk("key_usage"); ok {
			data.Params.KeyUsage = x509.KeyUsage(parseKeyUsages(rawKeyUsageValue.([]string)))
		}

		if rawExtKeyUsagesValue, ok := input.apiData.GetOk("ext_key_usage"); ok {
			data.Params.ExtKeyUsage = parseExtKeyUsagesValue(0, rawExtKeyUsagesValue.([]string))
		}

		if rawExtKeyUsageOidsValue, ok := input.apiData.GetOk("ext_key_usage_oids"); ok {
			data.Params.ExtKeyUsage = parseExtKeyUsagesValue(0, rawExtKeyUsageOidsValue.([]string))
		}

		if data.SigningBundle == nil {
			// Generating a self-signed root certificate. Since we have no
			// issuer entry yet, we default to the global URLs.
			entries, err := getGlobalAIAURLs(ctx, sc.Storage)
			if err != nil {
				return nil, nil, errutil.InternalError{Err: fmt.Sprintf("unable to fetch AIA URL information: %v", err)}
			}

			uris, err := entries.toURLEntries(sc, issuerID(""))
			if err != nil {
				// When generating root issuers, don't err on missing issuer
				// ID; there is little value in including AIA info on a root,
				// as this info would point back to itself; though RFC 5280 is
				// a touch vague on this point, this seems to be consensus
				// from public CAs such as DigiCert Global Root G3, ISRG Root
				// X1, and others.
				//
				// This is a UX bug if we do err here, as it requires AIA
				// templating to not include issuer id (a best practice for
				// child certs issued from root and intermediate mounts
				// however), and setting this before root generation (or, on
				// root renewal) could cause problems.
				if _, nonEmptyIssuerErr := entries.toURLEntries(sc, issuerID("empty-issuer-id")); nonEmptyIssuerErr != nil {
					return nil, nil, errutil.InternalError{Err: fmt.Sprintf("unable to parse AIA URL information: %v\nUsing templated AIA URL's {{issuer_id}} field when generating root certificates is not supported.", err)}
				}

				uris = &certutil.URLEntries{}

				msg := "When generating root CA, found global AIA configuration with issuer_id template unsuitable for root generation. This AIA configuration has been ignored. To include AIA on this root CA, set the global AIA configuration to not include issuer_id and instead to refer to a static issuer name."
				warnings = append(warnings, msg)
			}

			data.Params.URLs = uris

			if input.role.MaxPathLength == nil {
				data.Params.MaxPathLength = -1
			} else {
				data.Params.MaxPathLength = *input.role.MaxPathLength
			}
		}
	}

	parsedBundle, err := generateCABundle(sc, input, data, randomSource)
	if err != nil {
		return nil, nil, err
	}

	return parsedBundle, warnings, nil
}

// Generate a certificate evaluating params against CEL role
func generateCELCert(
	evaluationData map[string]interface{},
	caSign *certutil.CAInfoBundle,
	cert *x509.Certificate,
	randomSource io.Reader,
) (*certutil.ParsedCertBundle, error) {
	parsedBundle, err := certutil.CreateCertificateWithTemplate(caSign, evaluationData, *cert, randomSource)
	if err != nil {
		return nil, err
	}
	return parsedBundle, nil
}

// Generate a certificate evaluating params against CEL role
func signCELCert(
	evaluationData map[string]interface{},
	caSign *certutil.CAInfoBundle,
	cert *x509.Certificate,
	csr *x509.CertificateRequest,
) (*certutil.ParsedCertBundle, error) {
	parsedBundle, err := certutil.SignCertificateWithTemplate(caSign, csr, evaluationData, *cert)
	if err != nil {
		return nil, err
	}
	return parsedBundle, nil
}

// N.B.: This is only meant to be used for generating intermediate CAs.
// It skips some sanity checks.
func generateIntermediateCSR(sc *storageContext, input *inputBundle, randomSource io.Reader) (*certutil.ParsedCSRBundle, []string, error) {
	b := sc.Backend

	creation, warnings, err := generateCreationBundle(b, input, nil, nil)
	if err != nil {
		return nil, nil, err
	}
	if creation.Params == nil {
		return nil, nil, errutil.InternalError{Err: "nil parameters received from parameter bundle generation"}
	}

	addBasicConstraints := input.apiData != nil && input.apiData.Get("add_basic_constraints").(bool)
	parsedBundle, err := generateCSRBundle(sc, input, creation, addBasicConstraints, randomSource)
	if err != nil {
		return nil, nil, err
	}

	return parsedBundle, warnings, nil
}

func signCert(b *backend,
	data *inputBundle,
	caSign *certutil.CAInfoBundle,
	isCA bool,
	useCSRValues bool) (*certutil.ParsedCertBundle, []string, error,
) {
	if data.role == nil {
		return nil, nil, errutil.InternalError{Err: "no role found in data bundle"}
	}

	csrString := data.apiData.Get("csr").(string)
	if csrString == "" {
		return nil, nil, errutil.UserError{Err: "\"csr\" is empty"}
	}

	pemBlock, _ := pem.Decode([]byte(csrString))
	if pemBlock == nil {
		return nil, nil, errutil.UserError{Err: "csr contains no data"}
	}
	csr, err := x509.ParseCertificateRequest(pemBlock.Bytes)
	if err != nil {
		return nil, nil, errutil.UserError{Err: fmt.Sprintf("certificate request could not be parsed: %v", err)}
	}

	if csr.PublicKeyAlgorithm == x509.UnknownPublicKeyAlgorithm || csr.PublicKey == nil {
		return nil, nil, errutil.UserError{Err: "Refusing to sign CSR with empty PublicKey. This usually means the SubjectPublicKeyInfo field has an OID not recognized by Go, such as 1.2.840.113549.1.1.10 for rsaPSS."}
	}

	// This switch validates that the CSR key type matches the role and sets
	// the value in the actualKeyType/actualKeyBits values.
	actualKeyType := ""
	actualKeyBits := 0

	switch data.role.KeyType {
	case "rsa":
		// Verify that the key matches the role type
		if csr.PublicKeyAlgorithm != x509.RSA {
			return nil, nil, errutil.UserError{Err: fmt.Sprintf(
				"role requires keys of type %s",
				data.role.KeyType,
			)}
		}

		pubKey, ok := csr.PublicKey.(*rsa.PublicKey)
		if !ok {
			return nil, nil, errutil.UserError{Err: "could not parse CSR's public key"}
		}

		actualKeyType = "rsa"
		actualKeyBits = pubKey.N.BitLen()
	case "ec":
		// Verify that the key matches the role type
		if csr.PublicKeyAlgorithm != x509.ECDSA {
			return nil, nil, errutil.UserError{Err: fmt.Sprintf(
				"role requires keys of type %s",
				data.role.KeyType,
			)}
		}
		pubKey, ok := csr.PublicKey.(*ecdsa.PublicKey)
		if !ok {
			return nil, nil, errutil.UserError{Err: "could not parse CSR's public key"}
		}

		actualKeyType = "ec"
		actualKeyBits = pubKey.Params().BitSize
	case "ed25519":
		// Verify that the key matches the role type
		if csr.PublicKeyAlgorithm != x509.Ed25519 {
			return nil, nil, errutil.UserError{Err: fmt.Sprintf(
				"role requires keys of type %s",
				data.role.KeyType,
			)}
		}

		_, ok := csr.PublicKey.(ed25519.PublicKey)
		if !ok {
			return nil, nil, errutil.UserError{Err: "could not parse CSR's public key"}
		}

		actualKeyType = "ed25519"
		actualKeyBits = 0
	case "any":
		// We need to compute the actual key type and key bits, to correctly
		// validate minimums and SignatureBits below.
		switch csr.PublicKeyAlgorithm {
		case x509.RSA:
			pubKey, ok := csr.PublicKey.(*rsa.PublicKey)
			if !ok {
				return nil, nil, errutil.UserError{Err: "could not parse CSR's public key"}
			}
			if pubKey.N.BitLen() < 2048 {
				return nil, nil, errutil.UserError{Err: "RSA keys < 2048 bits are unsafe and not supported"}
			}

			actualKeyType = "rsa"
			actualKeyBits = pubKey.N.BitLen()
		case x509.ECDSA:
			pubKey, ok := csr.PublicKey.(*ecdsa.PublicKey)
			if !ok {
				return nil, nil, errutil.UserError{Err: "could not parse CSR's public key"}
			}

			actualKeyType = "ec"
			actualKeyBits = pubKey.Params().BitSize
		case x509.Ed25519:
			_, ok := csr.PublicKey.(ed25519.PublicKey)
			if !ok {
				return nil, nil, errutil.UserError{Err: "could not parse CSR's public key"}
			}

			actualKeyType = "ed25519"
			actualKeyBits = 0
		default:
			return nil, nil, errutil.UserError{Err: "Unknown key type in CSR: " + csr.PublicKeyAlgorithm.String()}
		}
	default:
		return nil, nil, errutil.InternalError{Err: fmt.Sprintf("unsupported key type value: %s", data.role.KeyType)}
	}

	// Before validating key lengths, update our KeyBits/SignatureBits based
	// on the actual CSR key type.
	if data.role.KeyType == "any" {
		// We update the value of KeyBits and SignatureBits here (from the
		// role), using the specified key type. This allows us to convert
		// the default value (0) for SignatureBits and KeyBits to a
		// meaningful value.
		//
		// We ignore the role's original KeyBits value if the KeyType is any
		// as legacy (pre-1.10) roles had default values that made sense only
		// for RSA keys (key_bits=2048) and the older code paths ignored the role value
		// set for KeyBits when KeyType was set to any. This also enforces the
		// docs saying when key_type=any, we only enforce our specified minimums
		// for signing operations
		if data.role.KeyBits, data.role.SignatureBits, err = certutil.ValidateDefaultOrValueKeyTypeSignatureLength(
			actualKeyType, 0, data.role.SignatureBits,
		); err != nil {
			return nil, nil, errutil.InternalError{Err: fmt.Sprintf("unknown internal error updating default values: %v", err)}
		}

		// We're using the KeyBits field as a minimum value below, and P-224 is safe
		// and a previously allowed value. However, the above call defaults
		// to P-256 as that's a saner default than P-224 (w.r.t. generation), so
		// override it here to allow 224 as the smallest size we permit.
		if actualKeyType == "ec" {
			data.role.KeyBits = 224
		}
	}

	// At this point, data.role.KeyBits and data.role.SignatureBits should both
	// be non-zero, for RSA and ECDSA keys. Validate the actualKeyBits based on
	// the role's values. If the KeyType was any, and KeyBits was set to 0,
	// KeyBits should be updated to 2048 unless some other value was chosen
	// explicitly.
	//
	// This validation needs to occur regardless of the role's key type, so
	// that we always validate both RSA and ECDSA key sizes.
	switch actualKeyType {
	case "rsa":
		if actualKeyBits < data.role.KeyBits {
			return nil, nil, errutil.UserError{Err: fmt.Sprintf(
				"role requires a minimum of a %d-bit key, but CSR's key is %d bits",
				data.role.KeyBits, actualKeyBits,
			)}
		}

		if actualKeyBits < 2048 {
			return nil, nil, errutil.UserError{Err: fmt.Sprintf(
				"OpenBao requires a minimum of a 2048-bit key, but CSR's key is %d bits",
				actualKeyBits,
			)}
		}
	case "ec":
		if actualKeyBits < data.role.KeyBits {
			return nil, nil, errutil.UserError{Err: fmt.Sprintf(
				"role requires a minimum of a %d-bit key, but CSR's key is %d bits",
				data.role.KeyBits,
				actualKeyBits,
			)}
		}
	}

	creation, warnings, err := generateCreationBundle(b, data, caSign, csr)
	if err != nil {
		return nil, nil, err
	}
	if creation.Params == nil {
		return nil, nil, errutil.InternalError{Err: "nil parameters received from parameter bundle generation"}
	}

	creation.Params.IsCA = isCA
	creation.Params.UseCSRValues = useCSRValues

	if isCA {
		creation.Params.PermittedDNSDomains = data.apiData.Get("permitted_dns_domains").([]string)

		if rawKeyUsageValue, ok := data.apiData.GetOk("key_usage"); ok {
			creation.Params.KeyUsage = x509.KeyUsage(parseKeyUsages(rawKeyUsageValue.([]string)))
		}

		if rawExtKeyUsagesValue, ok := data.apiData.GetOk("ext_key_usage"); ok {
			creation.Params.ExtKeyUsage = parseExtKeyUsagesValue(0, rawExtKeyUsagesValue.([]string))
		}

		if rawExtKeyUsageOidsValue, ok := data.apiData.GetOk("ext_key_usage_oids"); ok {
			creation.Params.ExtKeyUsage = parseExtKeyUsagesValue(0, rawExtKeyUsageOidsValue.([]string))
		}
	} else {
		for _, ext := range csr.Extensions {
			if ext.Id.Equal(certutil.ExtensionBasicConstraintsOID) && !data.role.BasicConstraintsValidForNonCA {
				warnings = append(warnings, "specified CSR contained a Basic Constraints extension that was ignored during issuance")
			}
		}
	}

	parsedBundle, err := certutil.SignCertificate(creation)
	if err != nil {
		return nil, nil, err
	}

	return parsedBundle, warnings, nil
}

// otherNameRaw describes a name related to a certificate which is not in one
// of the standard name formats. RFC 5280, 4.2.1.6:
//
//	OtherName ::= SEQUENCE {
//	     type-id    OBJECT IDENTIFIER,
//	     value      [0] EXPLICIT ANY DEFINED BY type-id }
type otherNameRaw struct {
	TypeID asn1.ObjectIdentifier
	Value  asn1.RawValue
}

type otherNameUtf8 struct {
	oid   string
	value string
}

// ExtractUTF8String returns the UTF8 string contained in the Value, or an error
// if none is present.
func (oraw *otherNameRaw) extractUTF8String() (*otherNameUtf8, error) {
	svalue := cryptobyte.String(oraw.Value.Bytes)
	var outTag cbbasn1.Tag
	var val cryptobyte.String
	read := svalue.ReadAnyASN1(&val, &outTag)

	if read && outTag == asn1.TagUTF8String {
		return &otherNameUtf8{oid: oraw.TypeID.String(), value: string(val)}, nil
	}
	return nil, errors.New("no UTF-8 string found in OtherName")
}

func (o otherNameUtf8) String() string {
	return fmt.Sprintf("%s;%s:%s", o.oid, "UTF-8", o.value)
}

func getOtherSANsFromX509Extensions(exts []pkix.Extension) ([]otherNameUtf8, error) {
	var ret []otherNameUtf8
	for _, ext := range exts {
		if !ext.Id.Equal(oidExtensionSubjectAltName) {
			continue
		}
		err := forEachSAN(ext.Value, func(tag int, data []byte) error {
			if tag != 0 {
				return nil
			}

			var other otherNameRaw
			_, err := asn1.UnmarshalWithParams(data, &other, "tag:0")
			if err != nil {
				return fmt.Errorf("could not parse requested other SAN: %w", err)
			}
			val, err := other.extractUTF8String()
			if err != nil {
				return err
			}
			ret = append(ret, *val)
			return nil
		})
		if err != nil {
			return nil, err
		}
	}

	return ret, nil
}

func forEachSAN(extension []byte, callback func(tag int, data []byte) error) error {
	// RFC 5280, 4.2.1.6

	// SubjectAltName ::= GeneralNames
	//
	// GeneralNames ::= SEQUENCE SIZE (1..MAX) OF GeneralName
	//
	// GeneralName ::= CHOICE {
	//      otherName                       [0]     OtherName,
	//      rfc822Name                      [1]     IA5String,
	//      dNSName                         [2]     IA5String,
	//      x400Address                     [3]     ORAddress,
	//      directoryName                   [4]     Name,
	//      ediPartyName                    [5]     EDIPartyName,
	//      uniformResourceIdentifier       [6]     IA5String,
	//      iPAddress                       [7]     OCTET STRING,
	//      registeredID                    [8]     OBJECT IDENTIFIER }
	var seq asn1.RawValue
	rest, err := asn1.Unmarshal(extension, &seq)
	if err != nil {
		return err
	} else if len(rest) != 0 {
		return errors.New("x509: trailing data after X.509 extension")
	}
	if !seq.IsCompound || seq.Tag != 16 || seq.Class != 0 {
		return asn1.StructuralError{Msg: "bad SAN sequence"}
	}

	rest = seq.Bytes
	for len(rest) > 0 {
		var v asn1.RawValue
		rest, err = asn1.Unmarshal(rest, &v)
		if err != nil {
			return err
		}

		if err := callback(v.Tag, v.FullBytes); err != nil {
			return err
		}
	}

	return nil
}

func dedupCommonNames(cnRaw string) []string {
	// Translated from go-secure-stdlib/strutil:
	//
	// https://github.com/hashicorp/go-secure-stdlib/blob/c651aeae0c80f35905cf5a275c55e494c0eae09f/strutil/strutil.go#L56-L67
	input := strings.TrimSpace(cnRaw)
	parsed := []string{}
	if input == "" {
		// Don't return nil
		return parsed
	}

	return strutil.RemoveDuplicatesStable(strings.Split(input, ","), false)
}

// generateCreationBundle is a shared function that reads parameters supplied
// from the various endpoints and generates a CreationParameters with the
// parameters that can be used to issue or sign
func generateCreationBundle(b *backend, data *inputBundle, caSign *certutil.CAInfoBundle, csr *x509.CertificateRequest) (*certutil.CreationBundle, []string, error) {
	// Read in names -- CN, DNS and email addresses
	var cn string
	var ridSerialNumber string
	var warnings []string
	dnsNames := []string{}
	emailAddresses := []string{}
	{
		if csr != nil && data.role.UseCSRCommonName {

... [truncated, file is 66433 chars]
```

### builtin/logical/pki/path_roles.go
```
// Copyright (c) HashiCorp, Inc.
// SPDX-License-Identifier: MPL-2.0

package pki

import (
	"context"
	"crypto/x509"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/http"
	"slices"
	"strings"
	"time"

	"github.com/hashicorp/go-secure-stdlib/parseutil"
	"github.com/openbao/openbao/sdk/v2/framework"
	"github.com/openbao/openbao/sdk/v2/helper/certutil"
	"github.com/openbao/openbao/sdk/v2/helper/consts"
	"github.com/openbao/openbao/sdk/v2/helper/errutil"
	"github.com/openbao/openbao/sdk/v2/logical"
)

func pathListRoles(b *backend) *framework.Path {
	return &framework.Path{
		Pattern: "roles/?$",

		DisplayAttrs: &framework.DisplayAttributes{
			OperationPrefix: operationPrefixPKI,
			OperationSuffix: "roles",
		},

		Fields: map[string]*framework.FieldSchema{
			"after": {
				Type:        framework.TypeString,
				Description: `Optional entry to list begin listing after, not required to exist.`,
			},
			"limit": {
				Type:        framework.TypeInt,
				Description: `Optional number of entries to return; defaults to all entries.`,
			},
		},

		Operations: map[logical.Operation]framework.OperationHandler{
			logical.ListOperation: &framework.PathOperation{
				Callback: b.pathRoleList,
				Responses: map[int][]framework.Response{
					http.StatusOK: {{
						Description: "OK",
						Fields: map[string]*framework.FieldSchema{
							"keys": {
								Type:        framework.TypeStringSlice,
								Description: "List of roles",
								Required:    true,
							},
						},
					}},
				},
			},
		},

		HelpSynopsis:    pathListRolesHelpSyn,
		HelpDescription: pathListRolesHelpDesc,
	}
}

func pathRoles(b *backend) *framework.Path {
	pathRolesResponseFields := map[string]*framework.FieldSchema{
		"ttl": {
			Type:     framework.TypeInt64,
			Required: true,
			Description: `The lease duration (validity period of the
certificate) if no specific lease duration is requested.
The lease duration controls the expiration of certificates
issued by this backend. Defaults to the system default
value or the value of max_ttl, whichever is shorter.`,
		},

		"max_ttl": {
			Type:     framework.TypeInt64,
			Required: true,
			Description: `The maximum allowed lease duration. If not
set, defaults to the system maximum lease TTL.`,
		},
		"allow_token_displayname": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `Whether to allow "localhost" and "localdomain"
as a valid common name in a request, independent of allowed_domains value.`,
		},

		"allow_localhost": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `Whether to allow "localhost" and "localdomain"
as a valid common name in a request, independent of allowed_domains value.`,
		},

		"allowed_domains": {
			Type:     framework.TypeCommaStringSlice,
			Required: true,
			Description: `Specifies the domains this role is allowed
to issue certificates for. This is used with the allow_bare_domains,
allow_subdomains, and allow_glob_domains to determine matches for the
common name, DNS-typed SAN entries, and Email-typed SAN entries of
certificates. See the documentation for more information. This parameter
accepts a comma-separated string or list of domains.`,
		},
		"allowed_domains_template": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, Allowed domains can be specified using identity template policies.
				Non-templated domains are also permitted.`,
		},
		"allow_bare_domains": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, clients can request certificates
for the base domains themselves, e.g. "example.com" of domains listed
in allowed_domains. This is a separate option as in some cases this can
be considered a security threat. See the documentation for more
information.`,
		},

		"allow_subdomains": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, clients can request certificates for
subdomains of domains listed in allowed_domains, including wildcard
subdomains. See the documentation for more information.`,
		},

		"allow_glob_domains": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, domains specified in allowed_domains
can include shell-style glob patterns, e.g. "ftp*.example.com".
See the documentation for more information.`,
		},

		"allow_wildcard_certificates": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, allows certificates with wildcards in
the common name to be issued, conforming to RFC 6125's Section 6.4.3; e.g.,
"*.example.net" or "b*z.example.net". See the documentation for more
information.`,
		},

		"allow_any_name": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, clients can request certificates for
any domain, regardless of allowed_domains restrictions.
See the documentation for more information.`,
		},

		"enforce_hostnames": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, only valid host names are allowed for
CN and DNS SANs, and the host part of email addresses. Defaults to true.`,
		},

		"allow_ip_sans": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, IP Subject Alternative Names are allowed.
Allowed IP ranges can be further restricted using allowed_ip_sans_cidr.`,
		},

		"allowed_ip_sans_cidr": {
			Type:     framework.TypeCommaStringSlice,
			Required: true,
			Description: `Specifies the IP CIDRs this role is allowed
to issue certificates for. This is used with the allow_ip_sans to 
determine matches for the common name, and IP-typed SAN entries of
certificates. See the documentation for more information. This parameter
accepts a comma-separated string or list of CIDR notated IPs.
Roles with no value allow all IP ranges; to disable IP sans entirely
set allow_ip_sans=false instead.`,
		},

		"allowed_uri_sans": {
			Type:     framework.TypeCommaStringSlice,
			Required: true,
			Description: `If set, an array of allowed URIs for URI Subject Alternative Names.
Any valid URI is accepted, these values support globbing.`,
		},

		"allowed_uri_sans_template": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, Allowed URI SANs can be specified using identity template policies.
				Non-templated URI SANs are also permitted.`,
		},

		"allowed_other_sans": {
			Type:        framework.TypeCommaStringSlice,
			Required:    true,
			Description: `If set, an array of allowed other names to put in SANs. These values support globbing and must be in the format <oid>;<type>:<value>. Currently only "utf8" is a valid type. All values, including globbing values, must use this syntax, with the exception being a single "*" which allows any OID and any value (but type must still be utf8).`,
		},

		"allowed_serial_numbers": {
			Type:        framework.TypeCommaStringSlice,
			Required:    true,
			Description: `If set, an array of allowed serial numbers to put in Subject. These values support globbing.`,
		},
		"allowed_user_ids": {
			Type:        framework.TypeCommaStringSlice,
			Description: `If set, an array of allowed user-ids to put in user system login name specified here: https://www.rfc-editor.org/rfc/rfc1274#section-9.3.1`,
		},
		"server_flag": {
			Type:    framework.TypeBool,
			Default: true,
			Description: `If set, certificates are flagged for server auth use.
Defaults to true. See also RFC 5280 Section 4.2.1.12.`,
		},

		"client_flag": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, certificates are flagged for client auth use.
Defaults to true. See also RFC 5280 Section 4.2.1.12.`,
		},

		"code_signing_flag": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, certificates are flagged for code signing
use. Defaults to false. See also RFC 5280 Section 4.2.1.12.`,
		},

		"email_protection_flag": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, certificates are flagged for email
protection use. Defaults to false. See also RFC 5280 Section 4.2.1.12.`,
		},

		"key_type": {
			Type:     framework.TypeString,
			Required: true,
			Description: `The type of key to use; defaults to RSA. "rsa"
"ec", "ed25519" and "any" are the only valid values.`,
		},

		"key_bits": {
			Type:     framework.TypeInt,
			Required: true,
			Description: `The number of bits to use. Allowed values are
0 (universal default); with rsa key_type: 2048 (default), 3072, or
4096; with ec key_type: 224, 256 (default), 384, or 521; ignored with
ed25519.`,
		},
		"signature_bits": {
			Type:     framework.TypeInt,
			Required: true,
			Description: `The number of bits to use in the signature
algorithm; accepts 256 for SHA-2-256, 384 for SHA-2-384, and 512 for
SHA-2-512. Defaults to 0 to automatically detect based on key length
(SHA-2-256 for RSA keys, and matching the curve size for NIST P-Curves).`,
		},
		"use_pss": {
			Type:     framework.TypeBool,
			Required: false,
			Description: `Whether or not to use PSS signatures when using a
RSA key-type issuer. Defaults to false.`,
		},
		"key_usage": {
			Type:     framework.TypeCommaStringSlice,
			Required: true,
			Description: `A comma-separated string or list of key usages (not extended
key usages). Valid values can be found at
https://golang.org/pkg/crypto/x509/#KeyUsage
-- simply drop the "KeyUsage" part of the name.
To remove all key usages from being set, set
this value to an empty list. See also RFC 5280
Section 4.2.1.3.`,
		},

		"ext_key_usage": {
			Type:     framework.TypeCommaStringSlice,
			Required: true,
			Description: `A comma-separated string or list of extended key usages. Valid values can be found at
https://golang.org/pkg/crypto/x509/#ExtKeyUsage
-- simply drop the "ExtKeyUsage" part of the name.
To remove all key usages from being set, set
this value to an empty list. See also RFC 5280
Section 4.2.1.12.`,
		},

		"ext_key_usage_oids": {
			Type:        framework.TypeCommaStringSlice,
			Required:    true,
			Description: `A comma-separated string or list of extended key usage oids.`,
		},

		"use_csr_common_name": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, when used with a signing profile,
the common name in the CSR will be used. This
does *not* include any requested Subject Alternative
Names; use use_csr_sans for that. Defaults to true.`,
		},

		"use_csr_sans": {
			Type:     framework.TypeBool,
			Required: true,
			Description: `If set, when used with a signing profile,
the SANs in the CSR will be used. This does *not*
include the Common Name (cn); use use_csr_common_name
for that. Defaults to true.`,
		},

		"ou": {
			Type: framework.TypeCommaStringSlice,
			Description: `If set, OU (OrganizationalUnit) will be set to
this value in certificates issued by this role.`,
		},

		"organization": {
			Type: framework.TypeCommaStringSlice,
			Description: `If set, O (Organization) will be set to
this value in certificates issued by this role.`,
		},

		"country": {
			Type: framework.TypeCommaStringSlice,
			Description: `If set, Country will be set to
this value in certificates issued by this role.`,
		},

		"locality": {
			Type: framework.TypeCommaStringSlice,
			Description: `If set, Locality will be set to
this value in certificates issued by this role.`,
		},

		"province": {
			Type: framework.TypeCommaStringSlice,
			Description: `If set, Province will be set to
this value in certificates issued by this role.`,
		},

		"street_address": {
			Type: framework.TypeCommaStringSlice,
			Description: `If set, Street Address will be set to
this value in certificates issued by this role.`,
		},

		"postal_code": {
			Type: framework.TypeCommaStringSlice,
			Description: `If set, Postal Code will be set to
this value in certificates issued by this role.`,
		},

		"generate_lease": {
			Type: framework.TypeBool,
			Description: `
If set, certificates issued/signed against this role will have OpenBao leases
attached to them. Defaults to "false". Certificates can be added to the CRL by
"bao revoke <lease_id>" when certificates are associated with leases.  It can
also be done using the "pki/revoke" endpoint. However, when lease generation is
disabled, invoking "pki/revoke" would be the only way to add the certificates
to the CRL.  When large number of certificates are generated with long
lifetimes, it is recommended that lease generation be disabled, as large amount of
leases adversely affect the startup time of OpenBao.`,
		},

		"no_store": {
			Type: framework.TypeBool,
			Description: `
If set, certificates issued/signed against this role will not be stored in the
storage backend. This can improve performance when issuing large numbers of 
certificates. However, certificates issued in this way cannot be enumerated
or revoked, so this option is recommended only for certificates that are
non-sensitive, or extremely short-lived. This option implies a value of "false"
for "generate_lease".`,
		},

		"require_cn": {
			Type:        framework.TypeBool,
			Description: `If set to false, makes the 'common_name' field optional while generating a certificate.`,
		},

		"cn_validations": {
			Type: framework.TypeCommaStringSlice,
			Description: `List of allowed validations to run against the
Common Name field. Values can include 'email' to validate the CN is a email
address, 'hostname' to validate the CN is a valid hostname (potentially
including wildcards). When multiple validations are specified, these take
OR semantics (either email OR hostname are allowed). The special value
'disabled' allows disabling all CN name validations, allowing for arbitrary
non-Hostname, non-Email address CNs.`,
		},

		"policy_identifiers": {
			Type: framework.TypeCommaStringSlice,
			Description: `A comma-separated string or list of policy OIDs, or a JSON list of qualified policy
information, which must include an oid, and may include a notice and/or cps url, using the form 
[{"oid"="1.3.6.1.4.1.7.8","notice"="I am a user Notice"}, {"oid"="1.3.6.1.4.1.32473.1.2.4 ","cps"="https://example.com"}].`,
		},

		"basic_constraints_valid_for_non_ca": {
			Type:        framework.TypeBool,
			Description: `Mark Basic Constraints valid when issuing non-CA certificates.`,
		},
		"not_before_duration": {
			Type:        framework.TypeInt64,
			Description: `The duration in seconds before now which the certificate needs to be backdated by.`,
		},
		"not_before": {
			Type: framework.TypeString,
			Description: `Set the not before field of the certificate with specified date value.
The value format should be given in UTC format YYYY-MM-ddTHH:MM:SSZ.`,
		},
		"not_before_bound": {
			Type:          framework.TypeString,
			Description:   `Set how not_before can be configured.`,
			AllowedValues: []interface{}{PermitNotBeforeBound.String(), DurationNotBeforeBound.String(), ForbidNotBeforeBound.String()},
			Default:       PermitNotBeforeBound.String(),
		},
		"not_after": {
			Type: framework.TypeString,
			Description: `Set the not after field of the certificate with specified date value.
The value format should be given in UTC format YYYY-MM-ddTHH:MM:SSZ.`,
		},
		"not_after_bound": {
			Type:          framework.TypeString,
			Description:   `Set how not_after can be configured.`,
			AllowedValues: []interface{}{PermitNotAfterBound.String(), ForbidNotAfterBound.String(), TTLNotAfterBound.String(), "an explicit timestamp"},
			Default:       PermitNotAfterBound.String(),
		},
		"issuer_ref": {
			Type: framework.TypeString,
			Description: `Reference to the issuer used to sign requests
serviced by this role.`,
		},
	}

	return &framework.Path{
		Pattern: "roles/" + framework.GenericNameRegex("name"),

		DisplayAttrs: &framework.DisplayAttributes{
			OperationPrefix: operationPrefixPKI,
			OperationSuffix: "role",
		},

		Fields: map[string]*framework.FieldSchema{
			"backend": {
				Type:        framework.TypeString,
				Description: "Backend Type",
			},

			"name": {
				Type:        framework.TypeString,
				Description: "Name of the role",
			},

			"ttl": {
				Type: framework.TypeDurationSecond,
				Description: `The lease duration (validity period of the
certificate) if no specific lease duration is requested.
The lease duration controls the expiration of certificates
issued by this backend. Defaults to the system default
value or the value of max_ttl, whichever is shorter.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "TTL",
				},
			},

			"max_ttl": {
				Type: framework.TypeDurationSecond,
				Description: `The maximum allowed lease duration. If not
set, defaults to the system maximum lease TTL.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Max TTL",
				},
			},

			"allow_localhost": {
				Type:    framework.TypeBool,
				Default: true,
				Description: `Whether to allow "localhost" and "localdomain"
as a valid common name in a request, independent of allowed_domains value.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Value: true,
				},
			},

			"allowed_domains": {
				Type: framework.TypeCommaStringSlice,
				Description: `Specifies the domains this role is allowed
to issue certificates for. This is used with the allow_bare_domains,
allow_subdomains, and allow_glob_domains to determine matches for the
common name, DNS-typed SAN entries, and Email-typed SAN entries of
certificates. See the documentation for more information. This parameter
accepts a comma-separated string or list of domains.`,
			},
			"allowed_domains_template": {
				Type: framework.TypeBool,
				Description: `If set, Allowed domains can be specified using identity template policies.
				Non-templated domains are also permitted.`,
				Default: false,
			},
			"allow_bare_domains": {
				Type: framework.TypeBool,
				Description: `If set, clients can request certificates
for the base domains themselves, e.g. "example.com" of domains listed
in allowed_domains. This is a separate option as in some cases this can
be considered a security threat. See the documentation for more
information.`,
			},

			"allow_subdomains": {
				Type: framework.TypeBool,
				Description: `If set, clients can request certificates for
subdomains of domains listed in allowed_domains, including wildcard
subdomains. See the documentation for more information.`,
			},

			"allow_glob_domains": {
				Type: framework.TypeBool,
				Description: `If set, domains specified in allowed_domains
can include shell-style glob patterns, e.g. "ftp*.example.com".
See the documentation for more information.`,
			},

			"allow_wildcard_certificates": {
				Type: framework.TypeBool,
				Description: `If set, allows certificates with wildcards in
the common name to be issued, conforming to RFC 6125's Section 6.4.3; e.g.,
"*.example.net" or "b*z.example.net". See the documentation for more
information.`,
				Default: true,
			},

			"allow_any_name": {
				Type: framework.TypeBool,
				Description: `If set, clients can request certificates for
any domain, regardless of allowed_domains restrictions.
See the documentation for more information.`,
			},

			"enforce_hostnames": {
				Type:    framework.TypeBool,
				Default: true,
				Description: `If set, only valid host names are allowed for
CN and DNS SANs, and the host part of email addresses. Defaults to true.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Value: true,
				},
			},

			"allow_ip_sans": {
				Type:    framework.TypeBool,
				Default: true,
				Description: `If set, IP Subject Alternative Names are allowed.
Allowed IP ranges can be further restricted using allowed_ip_sans_cidr.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name:  "Allow IP Subject Alternative Names",
					Value: true,
				},
			},

			"allowed_ip_sans_cidr": {
				Type: framework.TypeCommaStringSlice,
				Description: `Specifies the IP CIDRs this role is allowed
to issue certificates for. This is used with the allow_ip_sans to 
determine matches for the common name, and IP-typed SAN entries of
certificates. See the documentation for more information. This parameter
accepts a comma-separated string or list of CIDR notated IPs.`,
			},

			"allowed_uri_sans": {
				Type: framework.TypeCommaStringSlice,
				Description: `If set, an array of allowed URIs for URI Subject Alternative Names.
Any valid URI is accepted, these values support globbing.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Allowed URI Subject Alternative Names",
				},
			},

			"allowed_uri_sans_template": {
				Type: framework.TypeBool,
				Description: `If set, Allowed URI SANs can be specified using identity template policies.
				Non-templated URI SANs are also permitted.`,
				Default: false,
			},

			"allowed_other_sans": {
				Type:        framework.TypeCommaStringSlice,
				Description: `If set, an array of allowed other names to put in SANs. These values support globbing and must be in the format <oid>;<type>:<value>. Currently only "utf8" is a valid type. All values, including globbing values, must use this syntax, with the exception being a single "*" which allows any OID and any value (but type must still be utf8).`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Allowed Other Subject Alternative Names",
				},
			},

			"allowed_serial_numbers": {
				Type:        framework.TypeCommaStringSlice,
				Description: `If set, an array of allowed serial numbers to put in Subject. These values support globbing.`,
			},

			"allowed_user_ids": {
				Type:        framework.TypeCommaStringSlice,
				Description: `If set, an array of allowed user-ids to put in user system login name specified here: https://www.rfc-editor.org/rfc/rfc1274#section-9.3.1`,
			},

			"server_flag": {
				Type:    framework.TypeBool,
				Default: true,
				Description: `If set, certificates are flagged for server auth use.
Defaults to true. See also RFC 5280 Section 4.2.1.12.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Value: true,
				},
			},

			"client_flag": {
				Type:    framework.TypeBool,
				Default: true,
				Description: `If set, certificates are flagged for client auth use.
Defaults to true. See also RFC 5280 Section 4.2.1.12.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Value: true,
				},
			},

			"code_signing_flag": {
				Type: framework.TypeBool,
				Description: `If set, certificates are flagged for code signing
use. Defaults to false. See also RFC 5280 Section 4.2.1.12.`,
			},

			"email_protection_flag": {
				Type: framework.TypeBool,
				Description: `If set, certificates are flagged for email
protection use. Defaults to false. See also RFC 5280 Section 4.2.1.12.`,
			},

			"key_type": {
				Type:    framework.TypeString,
				Default: "rsa",
				Description: `The type of key to use; defaults to RSA. "rsa"
"ec", "ed25519" and "any" are the only valid values.`,
				AllowedValues: []interface{}{"rsa", "ec", "ed25519", "any"},
			},

			"key_bits": {
				Type:    framework.TypeInt,
				Default: 0,
				Description: `The number of bits to use. Allowed values are
0 (universal default); with rsa key_type: 2048 (default), 3072, or
4096; with ec key_type: 224, 256 (default), 384, or 521; ignored with
ed25519.`,
			},

			"signature_bits": {
				Type:    framework.TypeInt,
				Default: 0,
				Description: `The number of bits to use in the signature
algorithm; accepts 256 for SHA-2-256, 384 for SHA-2-384, and 512 for
SHA-2-512. Defaults to 0 to automatically detect based on key length
(SHA-2-256 for RSA keys, and matching the curve size for NIST P-Curves).`,
			},

			"use_pss": {
				Type:    framework.TypeBool,
				Default: false,
				Description: `Whether or not to use PSS signatures when using a
RSA key-type issuer. Defaults to false.`,
			},

			"key_usage": {
				Type:    framework.TypeCommaStringSlice,
				Default: []string{"DigitalSignature", "KeyAgreement", "KeyEncipherment"},
				Description: `A comma-separated string or list of key usages (not extended
key usages). Valid values can be found at
https://golang.org/pkg/crypto/x509/#KeyUsage
-- simply drop the "KeyUsage" part of the name.
To remove all key usages from being set, set
this value to an empty list. See also RFC 5280
Section 4.2.1.3.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Value: "DigitalSignature,KeyAgreement,KeyEncipherment",
				},
			},

			"ext_key_usage": {
				Type:    framework.TypeCommaStringSlice,
				Default: []string{},
				Description: `A comma-separated string or list of extended key usages. Valid values can be found at
https://golang.org/pkg/crypto/x509/#ExtKeyUsage
-- simply drop the "ExtKeyUsage" part of the name.
To remove all key usages from being set, set
this value to an empty list. See also RFC 5280
Section 4.2.1.12.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Extended Key Usage",
				},
			},

			"ext_key_usage_oids": {
				Type:        framework.TypeCommaStringSlice,
				Description: `A comma-separated string or list of extended key usage oids.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Extended Key Usage OIDs",
				},
			},

			"use_csr_common_name": {
				Type:    framework.TypeBool,
				Default: true,
				Description: `If set, when used with a signing profile,
the common name in the CSR will be used. This
does *not* include any requested Subject Alternative
Names; use use_csr_sans for that. Defaults to true.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name:  "Use CSR Common Name",
					Value: true,
				},
			},

			"use_csr_sans": {
				Type:    framework.TypeBool,
				Default: true,
				Description: `If set, when used with a signing profile,
the SANs in the CSR will be used. This does *not*
include the Common Name (cn); use use_csr_common_name
for that. Defaults to true.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name:  "Use CSR Subject Alternative Names",
					Value: true,
				},
			},

			"ou": {
				Type: framework.TypeCommaStringSlice,
				Description: `If set, OU (OrganizationalUnit) will be set to
this value in certificates issued by this role.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Organizational Unit",
				},
			},

			"organization": {
				Type: framework.TypeCommaStringSlice,
				Description: `If set, O (Organization) will be set to
this value in certificates issued by this role.`,
			},

			"country": {
				Type: framework.TypeCommaStringSlice,
				Description: `If set, Country will be set to
this value in certificates issued by this role.`,
			},

			"locality": {
				Type: framework.TypeCommaStringSlice,
				Description: `If set, Locality will be set to
this value in certificates issued by this role.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Locality/City",
				},
			},

			"province": {
				Type: framework.TypeCommaStringSlice,
				Description: `If set, Province will be set to
this value in certificates issued by this role.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Province/State",
				},
			},

			"street_address": {
				Type: framework.TypeCommaStringSlice,
				Description: `If set, Street Address will be set to
this value in certificates issued by this role.`,
			},

			"postal_code": {
				Type: framework.TypeCommaStringSlice,
				Description: `If set, Postal Code will be set to
this value in certificates issued by this role.`,
			},

			"generate_lease": {
				Type: framework.TypeBool,
				Description: `
If set, certificates issued/signed against this role will have OpenBao leases
attached to them. Defaults to "false". Certificates can be added to the CRL by
"bao revoke <lease_id>" when certificates are associated with leases.  It can
also be done using the "pki/revoke" endpoint. However, when lease generation is
disabled, invoking "pki/revoke" would be the only way to add the certificates
to the CRL.  When large number of certificates are generated with long
lifetimes, it is recommended that lease generation be disabled, as large amount of
leases adversely affect the startup time of OpenBao.`,
			},

			"no_store": {
				Type: framework.TypeBool,
				Description: `
If set, certificates issued/signed against this role will not be stored in the
storage backend. This can improve performance when issuing large numbers of 
certificates. However, certificates issued in this way cannot be enumerated
or revoked, so this option is recommended only for certificates that are
non-sensitive, or extremely short-lived. This option implies a value of "false"
for "generate_lease".`,
			},

			"require_cn": {
				Type:        framework.TypeBool,
				Default:     true,
				Description: `If set to false, makes the 'common_name' field optional while generating a certificate.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Require Common Name",
				},
			},

			"cn_validations": {
				Type:    framework.TypeCommaStringSlice,
				Default: []string{"email", "hostname"},
				Description: `List of allowed validations to run against the
Common Name field. Values can include 'email' to validate the CN is a email
address, 'hostname' to validate the CN is a valid hostname (potentially
including wildcards). When multiple validations are specified, these take
OR semantics (either email OR hostname are allowed). The special value
'disabled' allows disabling all CN name validations, allowing for arbitrary
non-Hostname, non-Email address CNs.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Common Name Validations",
				},
			},

			"policy_identifiers": {
				Type: framework.TypeCommaStringSlice,
				Description: `A comma-separated string or list of policy OIDs, or a JSON list of qualified policy
information, which must include an oid, and may include a notice and/or cps url, using the form 
[{"oid"="1.3.6.1.4.1.7.8","notice"="I am a user Notice"}, {"oid"="1.3.6.1.4.1.32473.1.2.4 ","cps"="https://example.com"}].`,
			},

			"basic_constraints_valid_for_non_ca": {
				Type:        framework.TypeBool,
				Description: `Mark Basic Constraints valid when issuing non-CA certificates.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Basic Constraints Valid for Non-CA",
				},
			},
			"not_before_duration": {
				Type:        framework.TypeDurationSecond,
				Default:     30,
				Description: `The duration before now which the certificate needs to be backdated by.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Value: 30,
				},
			},
			"not_before": {
				Type: framework.TypeString,
				Description: `Set the not before field of the certificate with specified date value.
The value format should be given in UTC format YYYY-MM-ddTHH:MM:SSZ.`,
			},
			"not_before_bound": {
				Type:          framework.TypeString,
				Description:   `Set how not_before can be configured.`,
				AllowedValues: []interface{}{PermitNotBeforeBound.String(), DurationNotBeforeBound.String(), ForbidNotBeforeBound.String()},
				Default:       PermitNotBeforeBound.String(),
			},
			"not_after": {
				Type: framework.TypeString,
				Description: `Set the not after field of the certificate with specified date value.
The value format should be given in UTC format YYYY-MM-ddTHH:MM:SSZ.`,
			},
			"not_after_bound": {
				Type:          framework.TypeString,
				Description:   `Set how not_after can be configured.`,
				AllowedValues: []interface{}{PermitNotAfterBound.String(), TTLNotAfterBound.String(), ForbidNotAfterBound.String(), "an explicit timestamp"},
				Default:       PermitNotAfterBound.String(),
			},
			"issuer_ref": {
				Type: framework.TypeString,
				Description: `Reference to the issuer used to sign requests
serviced by this role.`,
				Default: defaultRef,
			},
		},

		Operations: map[logical.Operation]framework.OperationHandler{
			logical.ReadOperation: &framework.PathOperation{
				Callback: b.pathRoleRead,
				Responses: map[int][]framework.Response{
					http.StatusOK: {{
						Description: "OK",
						Fields:      pathRolesResponseFields,
					}},
				},
			},
			logical.UpdateOperation: &framework.PathOperation{
				Callback: b.pathRoleCreate,
				Responses: map[int][]framework.Response{
					http.StatusOK: {{
						Description: "OK",
						Fields:      pathRolesResponseFields,
					}},
				},
				// Read more about why these flags are set in backend.go.
				ForwardPerformanceStandby:   true,
				ForwardPerformanceSecondary: true,
			},
			logical.DeleteOperation: &framework.PathOperation{
				Callback: b.pathRoleDelete,
				Responses: map[int][]framework.Response{
					http.StatusNoContent: {{
						Description: "No Content",
					}},
				},
				// Read more about why these flags are set in backend.go.
				ForwardPerformanceStandby:   true,
				ForwardPerformanceSecondary: true,
			},
			logical.PatchOperation: &framework.PathOperation{
				Callback: b.pathRolePatch,
				Responses: map[int][]framework.Response{
					http.StatusOK: {{
						Description: "OK",
						Fields:      pathRolesResponseFields,
					}},
				},
				// Read more about why these flags are set in backend.go.
				ForwardPerformanceStandby:   true,
				ForwardPerformanceSecondary: true,
			},
		},

		HelpSynopsis:    pathRoleHelpSyn,
		HelpDescription: pathRoleHelpDesc,
	}
}

func (b *backend) getRole(ctx context.Context, s logical.Storage, n string) (*roleEntry, error) {
	entry, err := s.Get(ctx, "role/"+n)
	if err != nil {
		return nil, err
	}
	if entry == nil {
		return nil, nil
	}

	var result roleEntry
	if err := entry.DecodeJSON(&result); err != nil {
		return nil, err
	}

	// Migrate existing saved entries and save back if changed
	modified := false
	if len(result.DeprecatedTTL) == 0 && len(result.Lease) != 0 {
		result.DeprecatedTTL = result.Lease
		result.Lease = ""
		modified = true
	}
	if result.TTL == 0 && len(result.DeprecatedTTL) != 0 {
		parsed, err := parseutil.ParseDurationSecond(result.DeprecatedTTL)
		if err != nil {
			return nil, err
		}
		result.TTL = parsed
		result.DeprecatedTTL = ""
		modified = true
	}
	if len(result.DeprecatedMaxTTL) == 0 && len(result.LeaseMax) != 0 {
		result.DeprecatedMaxTTL = result.LeaseMax
		result.LeaseMax = ""
		modified = true
	}
	if result.MaxTTL == 0 && len(result.DeprecatedMaxTTL) != 0 {
		parsed, err := parseutil.ParseDurationSecond(result.DeprecatedMaxTTL)
		if err != nil {
			return nil, err
		}
		result.MaxTTL = parsed
		result.DeprecatedMaxTTL = ""
		modified = true
	}
	if result.AllowBaseDomain {
		result.AllowBaseDomain = false
		result.AllowBareDomains = true
		modified = true
	}
	if result.AllowedDomainsOld != "" {
		result.AllowedDomains = strings.Split(result.AllowedDomainsOld, ",")
		result.AllowedDomainsOld = ""
		modified = true
	}
	if result.AllowedBaseDomain != "" {
		if !slices.Contains(result.AllowedDomains, result.AllowedBaseDomain) {
			result.AllowedDomains = append(result.AllowedDomains, result.AllowedBaseDomain)
		}
		result.AllowedBaseDomain = ""
		modified = true
	}
	if result.AllowWildcardCertificates == nil {
		// While not the most secure default, when AllowWildcardCertificates isn't
		// explicitly specified in the stored Role, we automatically upgrade it to
		// true to preserve compatibility with previous versions of Vault. Once this
		// field is set, this logic will not be triggered any more.
		result.AllowWildcardCertificates = new(bool)
		*result.AllowWildcardCertificates = true
		modified = true
	}

	// Upgrade generate_lease in role
	if result.GenerateLease == nil {
		// All the new roles will have GenerateLease always set to a value. A
		// nil value indicates that this role needs an upgrade. Set it to
		// `true` to not alter its current behavior.
		result.GenerateLease = new(bool)
		*result.GenerateLease = true
		modified = true
	}

	// Upgrade key usages
	if result.KeyUsageOld != "" {
		result.KeyUsage = strings.Split(result.KeyUsageOld, ",")
		result.KeyUsageOld = ""
		modified = true
	}

	// Upgrade OU
	if result.OUOld != "" {
		result.OU = strings.Split(result.OUOld, ",")
		result.OUOld = ""
		modified = true
	}

	// Upgrade Organization
	if result.OrganizationOld != "" {
		result.Organization = strings.Split(result.OrganizationOld, ",")
		result.OrganizationOld = ""
		modified = true
	}

	// Set the issuer field to default if not set. We want to do this
	// unconditionally as we should probably never have an empty issuer
	// on a stored roles.
	if len(result.Issuer) == 0 {
		result.Issuer = defaultRef
		modified = true
	}

	// Update CN Validations to be the present default, "email,hostname"
	if len(result.CNValidations) == 0 {
		result.CNValidations = []string{"email", "hostname"}
		modified = true
	}

	// Update not_after_bound, not_before_bound
	if result.NotAfterBound == "" {
		result.NotAfterBound = PermitNotAfterBound.String()
		modified = true
	}
	if result.NotBeforeBound == "" {
		result.NotBeforeBound = PermitNotBeforeBound.String()
		modified = true
	}

	// Ensure the role is valid after updating.
	_, err = validateRole(b, &result, ctx, s)
	if err != nil {
		return nil, err
	}

	if modified && (b.System().LocalMount() || !b.System().ReplicationState().HasState(consts.ReplicationPerformanceSecondary)) {
		jsonEntry, err := logical.StorageEntryJSON("role/"+n, &result)
		if err != nil {
			return nil, err
		}
		if err := s.Put(ctx, jsonEntry); err != nil {
			// Only perform upgrades on replication primary
			if !strings.Contains(err.Error(), logical.ErrReadOnly.Error()) {
				return nil, err
			}
		}
	}

	result.Name = n

	return &result, nil
}

func (b *backend) pathRoleDelete(ctx context.Context, req *logical.Request, data *framework.FieldData) (*logical.Response, error) {
	err := req.Storage.Delete(ctx, "role/"+data.Get("name").(string))
	if err != nil {
		return nil, err
	}

	return nil, nil
}

func (b *backend) pathRoleRead(ctx context.Context, req *logical.Request, data *framework.FieldData) (*logical.Response, error) {
	roleName := data.Get("name").(string)
	if roleName == "" {
		return logical.ErrorResponse("missing role name"), nil
	}

	role, err := b.getRole(ctx, req.Storage, roleName)
	if err != nil {
		return nil, err
	}
	if role == nil {
		return nil, nil
	}

	resp := &logical.Response{
		Data: role.ToResponseData(),
	}
	return resp, nil
}

func (b *backend) pathRoleList(ctx context.Context, req *logical.Request, data *framework.FieldData) (*logical.Response, error) {
	after := data.Get("after").(string)
	limit := data.Get("limit").(int)

	entries, err := req.Storage.ListPage(ctx, "role/", after, limit)
	if err != nil {
		return nil, err
	}

	return logical.ListResponse(entries), nil
}

func (b *backend) pathRoleCreate(ctx context.Context, req *logical.Request, data *framework.FieldData) (*logical.Response, error) {
	var err error
	name := data.Get("name").(string)

	entry := &roleEntry{
		MaxTTL:                        time.Duration(data.Get("max_ttl").(int)) * time.Second,
		TTL:                           time.Duration(data.Get("ttl").(int)) * time.Second,
		AllowLocalhost:                data.Get("allow_localhost").(bool),
		AllowedDomains:                data.Get("allowed_domains").([]string),
		AllowedDomainsTemplate:        data.Get("allowed_domains_template").(bool),
		AllowBareDomains:              data.Get("allow_bare_domains").(bool),
		AllowSubdomains:               data.Get("allow_subdomains").(bool),
		AllowGlobDomains:              data.Get("allow_glob_domains").(bool),
		AllowWildcardCertificates:     new(bool), // Handled specially below
		AllowAnyName:                  data.Get("allow_any_name").(bool),
		AllowedURISANsTemplate:        data.Get("allowed_uri_sans_template").(bool),
		EnforceHostnames:              data.Get("enforce_hostnames").(bool),
		AllowIPSANs:                   data.Get("allow_ip_sans").(bool),
		AllowedIPSANsCIDR:             nil, // Handled specially below
		AllowedURISANs:                data.Get("allowed_uri_sans").([]string),
		ServerFlag:                    data.Get("server_flag").(bool),
		ClientFlag:                    data.Get("client_flag").(bool),
		CodeSigningFlag:               data.Get("code_signing_flag").(b
... [truncated, file is 70174 chars]
```

### builtin/logical/ssh/path_issue_sign.go
```
// Copyright (c) HashiCorp, Inc.
// SPDX-License-Identifier: MPL-2.0

package ssh

import (
	"crypto/dsa"
	"crypto/ecdsa"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"errors"
	"fmt"
	"io"
	"regexp"
	"slices"
	"strconv"
	"strings"
	"time"

	"github.com/hashicorp/go-secure-stdlib/parseutil"
	"github.com/hashicorp/go-secure-stdlib/strutil"
	"github.com/openbao/openbao/sdk/v2/framework"
	"github.com/openbao/openbao/sdk/v2/helper/certutil"
	"github.com/openbao/openbao/sdk/v2/logical"
	"golang.org/x/crypto/ssh"
)

var containsTemplateRegex = regexp.MustCompile(`{{.+?}}`)

var ecCurveBitsToAlgoName = map[int]string{
	256: ssh.KeyAlgoECDSA256,
	384: ssh.KeyAlgoECDSA384,
	521: ssh.KeyAlgoECDSA521,
}

// If the algorithm is not found, it could be that we have a curve
// that we haven't added a constant for yet. But they could allow it
// (assuming x/crypto/ssh can parse it) via setting a ec: <keyBits>
// mapping rather than using a named SSH key type, so erring out here
// isn't advisable.

type creationBundle struct {
	KeyID           string
	ValidPrincipals []string
	PublicKey       ssh.PublicKey
	CertificateType uint32
	TTL             time.Duration
	Signer          ssh.Signer
	Role            *sshRole
	CriticalOptions map[string]string
	Extensions      map[string]string
}

func (b *backend) pathSignIssueCertificateHelper(sc *storageContext, req *logical.Request, data *framework.FieldData, role *sshRole, publicKey ssh.PublicKey) (*logical.Response, error) {
	txRollback, err := logical.StartTxStorage(sc.Context, req)
	if err != nil {
		return nil, err
	}
	defer txRollback()

	keyID, err := b.calculateKeyID(data, req, role, publicKey)
	if err != nil {
		return logical.ErrorResponse(err.Error()), nil
	}

	certificateType, err := b.calculateCertificateType(data, role)
	if err != nil {
		return logical.ErrorResponse(err.Error()), nil
	}

	var parsedPrincipals []string
	if certificateType == ssh.HostCert {
		parsedPrincipals, err = b.calculateValidPrincipals(data, req, role, "", role.AllowedDomains, role.AllowedDomainsTemplate, validateValidPrincipalForHosts(role))
		if err != nil {
			return logical.ErrorResponse(err.Error()), nil
		}
	} else {
		defaultPrincipal := role.DefaultUser
		if role.DefaultUserTemplate {
			defaultPrincipal, err = b.renderPrincipal(role.DefaultUser, req)
			if err != nil {
				return nil, err
			}
		}
		parsedPrincipals, err = b.calculateValidPrincipals(data, req, role, defaultPrincipal, role.AllowedUsers, role.AllowedUsersTemplate, slices.Contains)
		if err != nil {
			return logical.ErrorResponse(err.Error()), nil
		}
	}

	ttl, err := b.calculateTTL(data, role)
	if err != nil {
		return logical.ErrorResponse(err.Error()), nil
	}

	criticalOptions, err := b.calculateCriticalOptions(data, role)
	if err != nil {
		return logical.ErrorResponse(err.Error()), nil
	}

	extensions, addExtTemplatingWarning, err := b.calculateExtensions(data, req, role)
	if err != nil {
		return logical.ErrorResponse(err.Error()), nil
	}

	issuerId, err := sc.resolveIssuerReference(role.Issuer)
	if err != nil {
		return handleStorageContextErr(err)
	}

	issuer, err := sc.fetchIssuerById(issuerId)
	if err != nil {
		return handleStorageContextErr(err)
	}

	privateKey := issuer.PrivateKey

	signer, err := ssh.ParsePrivateKey([]byte(privateKey))
	if err != nil {
		return nil, fmt.Errorf("failed to parse stored CA private key: %w", err)
	}

	cBundle := creationBundle{
		KeyID:           keyID,
		PublicKey:       publicKey,
		Signer:          signer,
		ValidPrincipals: parsedPrincipals,
		TTL:             ttl,
		CertificateType: certificateType,
		Role:            role,
		CriticalOptions: criticalOptions,
		Extensions:      extensions,
	}

	certificate, err := cBundle.sign()
	if err != nil {
		return nil, err
	}

	signedSSHCertificate := ssh.MarshalAuthorizedKey(certificate)
	if len(signedSSHCertificate) == 0 {
		return nil, errors.New("error marshaling signed certificate")
	}

	response := &logical.Response{
		Data: map[string]interface{}{
			"serial_number": strconv.FormatUint(certificate.Serial, 16),
			"signed_key":    string(signedSSHCertificate),
			"issuer_id":     issuerId,
		},
	}

	if addExtTemplatingWarning {
		response.AddWarning("default_extension templating enabled with at least one extension requiring identity templating. However, this request lacked identity entity information, causing one or more extensions to be skipped from the generated certificate.")
	}

	if err := logical.EndTxStorage(sc.Context, req); err != nil {
		return nil, err
	}

	return response, nil
}

func (b *backend) renderPrincipal(principal string, req *logical.Request) (string, error) {
	// Look for templating markers {{ .* }}
	matched := containsTemplateRegex.MatchString(principal)
	if matched {
		if req.EntityID != "" {
			// Retrieve principal based on template + entityID from request.
			renderedPrincipal, err := framework.PopulateIdentityTemplate(principal, req.EntityID, b.System())
			if err != nil {
				return "", fmt.Errorf("template '%s' could not be rendered -> %s", principal, err)
			}
			return renderedPrincipal, nil
		}
	}
	// Static principal
	return principal, nil
}

func (b *backend) calculateValidPrincipals(data *framework.FieldData, req *logical.Request, role *sshRole, defaultPrincipal, principalsAllowedByRole string, enableTemplating bool, validatePrincipal func([]string, string) bool) ([]string, error) {
	validPrincipals := ""
	validPrincipalsRaw, ok := data.GetOk("valid_principals")
	if ok {
		validPrincipals = validPrincipalsRaw.(string)
	} else {
		validPrincipals = defaultPrincipal
	}

	parsedPrincipals := strutil.RemoveDuplicates(strutil.ParseStringSlice(validPrincipals, ","), false)
	// Build list of allowed Principals from template and static principalsAllowedByRole
	var allowedPrincipals []string
	if enableTemplating {
		rendered, err := b.renderPrincipal(principalsAllowedByRole, req)
		if err != nil {
			return nil, err
		}
		allowedPrincipals = strutil.RemoveDuplicates(strutil.ParseStringSlice(rendered, ","), false)
	} else {
		allowedPrincipals = strutil.RemoveDuplicates(strutil.ParseStringSlice(principalsAllowedByRole, ","), false)
	}

	switch {
	case len(parsedPrincipals) == 0:
		if !role.AllowEmptyPrincipals && principalsAllowedByRole != "*" {
			return nil, errors.New("refusing to issue unsafe, globally-valid certificate with no principals specified; set valid_principals or default_user")
		}

		// There is nothing to process
		return nil, nil
	case len(allowedPrincipals) == 0:
		// User has requested principals to be set, but role is not configured
		// with any principals
		return nil, errors.New("role is not configured to allow any principals")
	default:
		// Role was explicitly configured to allow any principal.
		if principalsAllowedByRole == "*" {
			return parsedPrincipals, nil
		}

		for _, principal := range parsedPrincipals {
			if !validatePrincipal(strutil.RemoveDuplicates(allowedPrincipals, false), principal) {
				return nil, fmt.Errorf("%v is not a valid value for valid_principals", principal)
			}
		}
		return parsedPrincipals, nil
	}
}

func validateValidPrincipalForHosts(role *sshRole) func([]string, string) bool {
	return func(allowedPrincipals []string, validPrincipal string) bool {
		for _, allowedPrincipal := range allowedPrincipals {
			if allowedPrincipal == validPrincipal && role.AllowBareDomains {
				return true
			}
			if role.AllowSubdomains && strings.HasSuffix(validPrincipal, "."+allowedPrincipal) {
				return true
			}
		}

		return false
	}
}

func (b *backend) calculateCertificateType(data *framework.FieldData, role *sshRole) (uint32, error) {
	requestedCertificateType := data.Get("cert_type").(string)

	var certificateType uint32
	switch requestedCertificateType {
	case "user":
		if !role.AllowUserCertificates {
			return 0, errors.New("cert_type 'user' is not allowed by role")
		}
		certificateType = ssh.UserCert
	case "host":
		if !role.AllowHostCertificates {
			return 0, errors.New("cert_type 'host' is not allowed by role")
		}
		certificateType = ssh.HostCert
	default:
		return 0, errors.New("cert_type must be either 'user' or 'host'")
	}

	return certificateType, nil
}

func (b *backend) calculateKeyID(data *framework.FieldData, req *logical.Request, role *sshRole, pubKey ssh.PublicKey) (string, error) {
	reqID := data.Get("key_id").(string)

	if reqID != "" {
		if !role.AllowUserKeyIDs {
			return "", errors.New("setting key_id is not allowed by role")
		}
		return reqID, nil
	}

	keyIDFormat := "vault-{{token_display_name}}-{{public_key_hash}}"
	if req.DisplayName == "" {
		keyIDFormat = "vault-{{public_key_hash}}"
	}

	if role.KeyIDFormat != "" {
		keyIDFormat = role.KeyIDFormat
	}

	keyID := substQuery(keyIDFormat, map[string]string{
		"token_display_name": req.DisplayName,
		"role_name":          data.Get("role").(string),
		"public_key_hash":    fmt.Sprintf("%x", sha256.Sum256(pubKey.Marshal())),
	})

	return keyID, nil
}

func (b *backend) calculateCriticalOptions(data *framework.FieldData, role *sshRole) (map[string]string, error) {
	unparsedCriticalOptions := data.Get("critical_options").(map[string]interface{})
	if len(unparsedCriticalOptions) == 0 {
		return role.DefaultCriticalOptions, nil
	}

	criticalOptions := convertMapToStringValue(unparsedCriticalOptions)

	if role.AllowedCriticalOptions != "" {
		notAllowedOptions := []string{}
		allowedCriticalOptions := strings.Split(role.AllowedCriticalOptions, ",")

		for option := range criticalOptions {
			if !slices.Contains(allowedCriticalOptions, option) {
				notAllowedOptions = append(notAllowedOptions, option)
			}
		}

		if len(notAllowedOptions) != 0 {
			return nil, fmt.Errorf("critical options not on allowed list: %v", notAllowedOptions)
		}
	}

	return criticalOptions, nil
}

func (b *backend) calculateExtensions(data *framework.FieldData, req *logical.Request, role *sshRole) (map[string]string, bool, error) {
	unparsedExtensions := data.Get("extensions").(map[string]interface{})
	extensions := make(map[string]string)

	if len(unparsedExtensions) > 0 {
		extensions := convertMapToStringValue(unparsedExtensions)
		if role.AllowedExtensions == "*" {
			// Allowed extensions was configured to allow all
			return extensions, false, nil
		}

		notAllowed := []string{}
		allowedExtensions := strings.Split(role.AllowedExtensions, ",")
		for extensionKey := range extensions {
			if !slices.Contains(allowedExtensions, extensionKey) {
				notAllowed = append(notAllowed, extensionKey)
			}
		}

		if len(notAllowed) != 0 {
			return nil, false, fmt.Errorf("extensions %v are not on allowed list", notAllowed)
		}
		return extensions, false, nil
	}

	haveMissingEntityInfoWithTemplatedExt := false

	if role.DefaultExtensionsTemplate {
		for extensionKey, extensionValue := range role.DefaultExtensions {
			// Look for templating markers {{ .* }}
			matched := containsTemplateRegex.MatchString(extensionValue)
			if matched {
				if req.EntityID != "" {
					// Retrieve extension value based on template + entityID from request.
					templateExtensionValue, err := framework.PopulateIdentityTemplate(extensionValue, req.EntityID, b.System())
					if err == nil {
						// Template returned an extension value that we can use
						extensions[extensionKey] = templateExtensionValue
					} else {
						return nil, false, fmt.Errorf("template '%s' could not be rendered -> %s", extensionValue, err)
					}
				} else {
					haveMissingEntityInfoWithTemplatedExt = true
				}
			} else {
				// Static extension value or err template
				extensions[extensionKey] = extensionValue
			}
		}
	} else {
		extensions = role.DefaultExtensions
	}

	return extensions, haveMissingEntityInfoWithTemplatedExt, nil
}

func (b *backend) calculateTTL(data *framework.FieldData, role *sshRole) (time.Duration, error) {
	var ttl, maxTTL time.Duration
	var err error

	ttlRaw, specifiedTTL := data.GetOk("ttl")
	if specifiedTTL {
		ttl = time.Duration(ttlRaw.(int)) * time.Second
	} else {
		ttl, err = parseutil.ParseDurationSecond(role.TTL)
		if err != nil {
			return 0, err
		}
	}
	if ttl == 0 {
		ttl = b.System().DefaultLeaseTTL()
	}

	maxTTL, err = parseutil.ParseDurationSecond(role.MaxTTL)
	if err != nil {
		return 0, err
	}
	if maxTTL == 0 {
		maxTTL = b.System().MaxLeaseTTL()
	}

	if ttl > maxTTL {
		// Don't error if they were using system defaults, only error if
		// they specifically chose a bad TTL
		if !specifiedTTL {
			ttl = maxTTL
		} else {
			return 0, fmt.Errorf("ttl is larger than maximum allowed %d", maxTTL/time.Second)
		}
	}

	return ttl, nil
}

func (b *backend) validateSignedKeyRequirements(publickey ssh.PublicKey, role *sshRole) error {
	if len(role.AllowedUserKeyTypesLengths) != 0 {
		var keyType string
		var keyBits int

		switch k := publickey.(type) {
		case ssh.CryptoPublicKey:
			ff := k.CryptoPublicKey()
			switch k := ff.(type) {
			case *rsa.PublicKey:
				keyType = "rsa"
				keyBits = k.N.BitLen()
			case *dsa.PublicKey:
				keyType = "dsa"
				keyBits = k.P.BitLen()
			case *ecdsa.PublicKey:
				keyType = "ecdsa"
				keyBits = k.Curve.Params().BitSize
			case ed25519.PublicKey:
				keyType = "ed25519"
			default:
				return fmt.Errorf("public key type of %s is not allowed", keyType)
			}
		default:
			return fmt.Errorf("pubkey not suitable for crypto (expected ssh.CryptoPublicKey but found %T)", k)
		}

		keyTypeToMapKey := createKeyTypeToMapKey(keyType, keyBits)

		var present bool
		var pass bool
		for _, kstr := range keyTypeToMapKey[keyType] {
			allowed_values, ok := role.AllowedUserKeyTypesLengths[kstr]
			if !ok {
				continue
			}

			present = true

			for _, value := range allowed_values {
				if keyType == "rsa" || keyType == "dsa" {
					// Regardless of map naming, we always need to validate the
					// bit length of RSA and DSA keys. Use the keyType flag to
					if keyBits == value {
						pass = true
					}
				} else if kstr == "ec" || kstr == "ecdsa" {
					// If the map string is "ecdsa", we have to validate the keyBits
					// are a match for an allowed value, meaning that our curve
					// is allowed. This isn't necessary when a named curve (e.g.
					// ssh.KeyAlgoECDSA256) is allowed (and hence kstr is that),
					// because keyBits is already specified in the kstr. Thus,
					// we have conditioned around kstr and not keyType (like with
					// rsa or dsa).
					if keyBits == value {
						pass = true
					}
				} else {
					// We get here in two cases: we have a algo-named EC key
					// matching a format specifier in the key map (e.g., a P-256
					// key with a KeyAlgoECDSA256 entry in the map) or we have a
					// ed25519 key (which is always allowed).
					pass = true
				}
			}
		}

		if !present {
			return fmt.Errorf("key of type %s is not allowed", keyType)
		}

		if !pass {
			return fmt.Errorf("key is of an invalid size: %v", keyBits)
		}
	}
	return nil
}

func (b *creationBundle) sign() (retCert *ssh.Certificate, retErr error) {
	defer func() {
		if r := recover(); r != nil {
			errMsg, ok := r.(string)
			if ok {
				retCert = nil
				retErr = errors.New(errMsg)
			}
		}
	}()

	serialNumber, err := certutil.GenerateSerialNumber()
	if err != nil {
		return nil, err
	}

	now := time.Now()

	sshAlgorithmSigner, ok := b.Signer.(ssh.AlgorithmSigner)
	if !ok {
		return nil, errors.New("failed to generate signed SSH key: signer is not an AlgorithmSigner")
	}

	// prepare certificate for signing
	nonce := make([]byte, 32)
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, fmt.Errorf("failed to generate signed SSH key: error generating random nonce: %w", err)
	}
	certificate := &ssh.Certificate{
		Serial:          serialNumber.Uint64(),
		Key:             b.PublicKey,
		KeyId:           b.KeyID,
		ValidPrincipals: b.ValidPrincipals,
		ValidAfter:      uint64(now.Add(-b.Role.NotBeforeDuration).In(time.UTC).Unix()),
		ValidBefore:     uint64(now.Add(b.TTL).In(time.UTC).Unix()),
		CertType:        b.CertificateType,
		Permissions: ssh.Permissions{
			CriticalOptions: b.CriticalOptions,
			Extensions:      b.Extensions,
		},
		Nonce:        nonce,
		SignatureKey: sshAlgorithmSigner.PublicKey(),
	}

	// get bytes to sign; this is based on Certificate.bytesForSigning() from the go ssh lib
	out := certificate.Marshal()
	// Drop trailing signature length.
	certificateBytes := out[:len(out)-4]

	algo := b.Role.AlgorithmSigner

	// Handle the new default algorithm selection process correctly.
	if algo == DefaultAlgorithmSigner && sshAlgorithmSigner.PublicKey().Type() == ssh.KeyAlgoRSA {
		algo = ssh.KeyAlgoRSASHA256
	} else if algo == DefaultAlgorithmSigner {
		algo = ""
	}

	sig, err := sshAlgorithmSigner.SignWithAlgorithm(rand.Reader, certificateBytes, algo)
	if err != nil {
		return nil, fmt.Errorf("failed to generate signed SSH key: sign error: %w", err)
	}

	certificate.Signature = sig

	return certificate, nil
}

func createKeyTypeToMapKey(keyType string, keyBits int) map[string][]string {
	keyTypeToMapKey := map[string][]string{
		"rsa":     {"rsa", ssh.KeyAlgoRSA},
		"dsa":     {"dsa", ssh.KeyAlgoDSA},
		"ecdsa":   {"ecdsa", "ec"},
		"ed25519": {"ed25519", ssh.KeyAlgoED25519},
	}

	if keyType == "ecdsa" {
		if algo, ok := ecCurveBitsToAlgoName[keyBits]; ok {
			keyTypeToMapKey[keyType] = append(keyTypeToMapKey[keyType], algo)
		}
	}

	return keyTypeToMapKey
}

```

### builtin/logical/ssh/path_roles.go
```
// Copyright (c) HashiCorp, Inc.
// SPDX-License-Identifier: MPL-2.0

package ssh

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/hashicorp/go-secure-stdlib/parseutil"
	"github.com/openbao/openbao/sdk/v2/framework"
	"github.com/openbao/openbao/sdk/v2/helper/cidrutil"
	"github.com/openbao/openbao/sdk/v2/helper/consts"
	"github.com/openbao/openbao/sdk/v2/logical"
	"golang.org/x/crypto/ssh"
)

const (
	// KeyTypeOTP is an key of type OTP
	KeyTypeOTP = "otp"
	// KeyTypeDynamic is dynamic key type; removed.
	KeyTypeDynamic = "dynamic"
	// KeyTypeCA is an key of type CA
	KeyTypeCA = "ca"

	// DefaultAlgorithmSigner is the default RSA signing algorithm
	DefaultAlgorithmSigner = "default"

	// Present version of the sshRole struct; when adding a new field or are
	// needing to perform a migration, increment this struct and read the note
	// in checkUpgrade(...).
	roleEntryVersion = 4
)

// Structure that represents a role in SSH backend. This is a common role structure
// for both OTP and CA roles. Not all the fields are mandatory for both type.
// Some are applicable for one and not for other. It doesn't matter.
type sshRole struct {
	KeyType                    string            `mapstructure:"key_type" json:"key_type"`
	DefaultUser                string            `mapstructure:"default_user" json:"default_user"`
	DefaultUserTemplate        bool              `mapstructure:"default_user_template" json:"default_user_template"`
	CIDRList                   string            `mapstructure:"cidr_list" json:"cidr_list"`
	ExcludeCIDRList            string            `mapstructure:"exclude_cidr_list" json:"exclude_cidr_list"`
	Port                       int               `mapstructure:"port" json:"port"`
	AllowedUsers               string            `mapstructure:"allowed_users" json:"allowed_users"`
	AllowedUsersTemplate       bool              `mapstructure:"allowed_users_template" json:"allowed_users_template"`
	AllowedDomains             string            `mapstructure:"allowed_domains" json:"allowed_domains"`
	AllowedDomainsTemplate     bool              `mapstructure:"allowed_domains_template" json:"allowed_domains_template"`
	MaxTTL                     string            `mapstructure:"max_ttl" json:"max_ttl"`
	TTL                        string            `mapstructure:"ttl" json:"ttl"`
	DefaultCriticalOptions     map[string]string `mapstructure:"default_critical_options" json:"default_critical_options"`
	DefaultExtensions          map[string]string `mapstructure:"default_extensions" json:"default_extensions"`
	DefaultExtensionsTemplate  bool              `mapstructure:"default_extensions_template" json:"default_extensions_template"`
	AllowedCriticalOptions     string            `mapstructure:"allowed_critical_options" json:"allowed_critical_options"`
	AllowedExtensions          string            `mapstructure:"allowed_extensions" json:"allowed_extensions"`
	AllowUserCertificates      bool              `mapstructure:"allow_user_certificates" json:"allow_user_certificates"`
	AllowHostCertificates      bool              `mapstructure:"allow_host_certificates" json:"allow_host_certificates"`
	AllowBareDomains           bool              `mapstructure:"allow_bare_domains" json:"allow_bare_domains"`
	AllowSubdomains            bool              `mapstructure:"allow_subdomains" json:"allow_subdomains"`
	AllowUserKeyIDs            bool              `mapstructure:"allow_user_key_ids" json:"allow_user_key_ids"`
	AllowEmptyPrincipals       bool              `mapstructure:"allow_empty_principals" json:"allow_empty_principals"`
	KeyIDFormat                string            `mapstructure:"key_id_format" json:"key_id_format"`
	OldAllowedUserKeyLengths   map[string]int    `mapstructure:"allowed_user_key_lengths" json:"allowed_user_key_lengths,omitempty"`
	AllowedUserKeyTypesLengths map[string][]int  `mapstructure:"allowed_user_key_types_lengths" json:"allowed_user_key_types_lengths"`
	AlgorithmSigner            string            `mapstructure:"algorithm_signer" json:"algorithm_signer"`
	Version                    int               `mapstructure:"role_version" json:"role_version"`
	NotBeforeDuration          time.Duration     `mapstructure:"not_before_duration" json:"not_before_duration"`
	Issuer                     string            `mapstructure:"issuer_ref" json:"issuer_ref"`
}

func pathListRoles(b *backend) *framework.Path {
	return &framework.Path{
		Pattern: "roles/?$",

		DisplayAttrs: &framework.DisplayAttributes{
			OperationPrefix: operationPrefixSSH,
			OperationSuffix: "roles",
		},

		Fields: map[string]*framework.FieldSchema{
			"after": {
				Type:        framework.TypeString,
				Description: `Optional entry to list begin listing after, not required to exist.`,
			},
			"limit": {
				Type:        framework.TypeInt,
				Description: `Optional number of entries to return; defaults to all entries.`,
			},
		},

		Operations: map[logical.Operation]framework.OperationHandler{
			logical.ListOperation: &framework.PathOperation{
				Callback: b.pathRoleList,
			},
		},

		HelpSynopsis:    pathRoleHelpSyn,
		HelpDescription: pathRoleHelpDesc,
	}
}

func pathRoles(b *backend) *framework.Path {
	return &framework.Path{
		Pattern: "roles/" + framework.GenericNameWithAtRegex("role"),

		DisplayAttrs: &framework.DisplayAttributes{
			OperationPrefix: operationPrefixSSH,
			OperationSuffix: "role",
		},

		Fields: map[string]*framework.FieldSchema{
			"role": {
				Type: framework.TypeString,
				Description: `
				[Required for all types]
				Name of the role being created.`,
			},
			"default_user": {
				Type: framework.TypeString,
				Description: `
				[Required for OTP type] [Optional for CA type]
				Default username for which a credential will be generated.
				When the endpoint 'creds/' is used without a username, this
				value will be used as default username.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Default Username",
				},
			},
			"default_user_template": {
				Type: framework.TypeBool,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				If set, Default user can be specified using identity template policies.
				Non-templated users are also permitted.
				`,
				Default: false,
			},
			"cidr_list": {
				Type: framework.TypeString,
				Description: `
				[Optional for OTP type] [Not applicable for CA type]
				Comma separated list of CIDR blocks for which the role is applicable for.
				CIDR blocks can belong to more than one role.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "CIDR List",
				},
			},
			"exclude_cidr_list": {
				Type: framework.TypeString,
				Description: `
				[Optional for OTP type] [Not applicable for CA type]
				Comma separated list of CIDR blocks. IP addresses belonging to these blocks are not
				accepted by the role. This is particularly useful when big CIDR blocks are being used
				by the role and certain parts of it needs to be kept out.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Exclude CIDR List",
				},
			},
			"port": {
				Type: framework.TypeInt,
				Description: `
				[Optional for OTP type] [Not applicable for CA type]
				Port number for SSH connection. Default is '22'. Port number does not
				play any role in creation of OTP. For 'otp' type, this is just a way
				to inform client about the port number to use. Port number will be
				returned to client by OpenBao server along with OTP.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Value: 22,
				},
			},
			"key_type": {
				Type: framework.TypeString,
				Description: `
				[Required for all types]
				Type of key used to login to hosts. It can be either 'otp' or 'ca'.
				'otp' type requires agent to be installed in remote hosts.`,
				AllowedValues: []interface{}{"otp", "ca"},
				DisplayAttrs: &framework.DisplayAttributes{
					Value: "ca",
				},
			},
			"allowed_users": {
				Type: framework.TypeString,
				Description: `
				[Optional for all types] [Works differently for CA type]
				If this option is not specified, or is '*', client can request a
				credential for any valid user at the remote host, including the
				admin user. If only certain usernames are to be allowed, then
				this list enforces it. If this field is set, then credentials
				can only be created for default_user and usernames present in
				this list. Setting this option will enable all the users with
				access to this role to fetch credentials for all other usernames
				in this list. Use with caution. N.B.: with the CA type, an empty
				list means that no users are allowed; explicitly specify '*' to
				allow any user.
				`,
			},
			"allowed_users_template": {
				Type: framework.TypeBool,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				If set, Allowed users can be specified using identity template policies.
				Non-templated users are also permitted.
				`,
				Default: false,
			},
			"allowed_domains": {
				Type: framework.TypeString,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				If this option is not specified, client can request for a signed certificate for any
				valid host. If only certain domains are allowed, then this list enforces it.
				`,
			},
			"allowed_domains_template": {
				Type: framework.TypeBool,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				If set, Allowed domains can be specified using identity template policies.
				Non-templated domains are also permitted.
				`,
				Default: false,
			},
			"ttl": {
				Type: framework.TypeDurationSecond,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				The lease duration if no specific lease duration is
				requested. The lease duration controls the expiration
				of certificates issued by this backend. Defaults to
				the value of max_ttl.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "TTL",
				},
			},
			"max_ttl": {
				Type: framework.TypeDurationSecond,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				The maximum allowed lease duration
				`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Max TTL",
				},
			},
			"allowed_critical_options": {
				Type: framework.TypeString,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				A comma-separated list of critical options that certificates can have when signed.
 				To allow any critical options, set this to an empty string.
				 `,
			},
			"allowed_extensions": {
				Type: framework.TypeString,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				A comma-separated list of extensions that certificates can have when signed.
				An empty list means that no extension overrides are allowed by an end-user; explicitly
				specify '*' to allow any extensions to be set.
				`,
			},
			"default_critical_options": {
				Type: framework.TypeMap,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				Critical options certificates should
				have if none are provided when signing. This field takes in key
				value pairs in JSON format.  Note that these are not restricted
				by "allowed_critical_options". Defaults to none.
				`,
			},
			"default_extensions": {
				Type: framework.TypeMap,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				Extensions certificates should have if
				none are provided when signing. This field takes in key value
				pairs in JSON format. Note that these are not restricted by
				"allowed_extensions". Defaults to none.
				`,
			},
			"default_extensions_template": {
				Type: framework.TypeBool,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				If set, Default extension values can be specified using identity template policies.
				Non-templated extension values are also permitted.
				`,
				Default: false,
			},
			"allow_user_certificates": {
				Type: framework.TypeBool,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				If set, certificates are allowed to be signed for use as a 'user'.
				`,
				Default: false,
			},
			"allow_host_certificates": {
				Type: framework.TypeBool,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				If set, certificates are allowed to be signed for use as a 'host'.
				`,
				Default: false,
			},
			"allow_bare_domains": {
				Type: framework.TypeBool,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				If set, host certificates that are requested are allowed to use the base domains listed in
				"allowed_domains", e.g. "example.com".
				This is a separate option as in some cases this can be considered a security threat.
				`,
			},
			"allow_subdomains": {
				Type: framework.TypeBool,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				If set, host certificates that are requested are allowed to use subdomains of those listed in "allowed_domains".
				`,
			},
			"allow_user_key_ids": {
				Type: framework.TypeBool,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				If true, users can override the key ID for a signed certificate with the "key_id" field.
				When false, the key ID will always be the token display name.
				The key ID is logged by the SSH server and can be useful for auditing.
				`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Allow User Key IDs",
				},
			},
			"key_id_format": {
				Type: framework.TypeString,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				When supplied, this value specifies a custom format for the key id of a signed certificate.
				The following variables are available for use: '{{token_display_name}}' - The display name of
				the token used to make the request. '{{role_name}}' - The name of the role signing the request.
				'{{public_key_hash}}' - A SHA256 checksum of the public key that is being signed.
				`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Key ID Format",
				},
			},
			"allowed_user_key_lengths": {
				Type: framework.TypeMap,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				If set, allows the enforcement of key types and minimum key sizes to be signed.
				`,
			},
			"algorithm_signer": {
				Type: framework.TypeString,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
				When supplied, this value specifies a signing algorithm for the key. Possible values:
				ssh-rsa, rsa-sha2-256, rsa-sha2-512, default, or the empty string.
				`,
				AllowedValues: []interface{}{"", DefaultAlgorithmSigner, ssh.KeyAlgoRSA, ssh.KeyAlgoRSASHA256, ssh.KeyAlgoRSASHA512},
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Signing Algorithm",
				},
			},
			"not_before_duration": {
				Type:    framework.TypeDurationSecond,
				Default: 30,
				Description: `
				[Not applicable for OTP type] [Optional for CA type]
   				The duration that the SSH certificate should be backdated by at issuance.`,
				DisplayAttrs: &framework.DisplayAttributes{
					Name:  "Not before duration",
					Value: 30,
				},
			},
			"allow_empty_principals": {
				Type: framework.TypeBool,
				Description: `
                [Optional for CA type]
				If true, host and user certificates can be issued without any valid principals. For
				host certificates, this means that any domain a host claims to be will be trusted by
				the connecting client. For user certificates, when a CA certificate is placed in a
				user's AuthorizedKeys file, any principal on that certificate will be allowed to
				connect. When allowed_users or allowed_domains is set to * (corresponding to the
				role/certificate type), allow_empty_principals=false still permits issuance.

				It is recommend to leave this disabled.
                `,
				DisplayAttrs: &framework.DisplayAttributes{
					Name: "Allow User Key IDs",
				},
			},
			"issuer_ref": {
				Type:        framework.TypeString,
				Description: `Reference to the issuer used to sign requests serviced by this role.`,
			},
		},

		Operations: map[logical.Operation]framework.OperationHandler{
			logical.ReadOperation: &framework.PathOperation{
				Callback: b.pathRoleRead,
			},
			logical.UpdateOperation: &framework.PathOperation{
				Callback: b.pathRoleWrite,
			},
			logical.DeleteOperation: &framework.PathOperation{
				Callback: b.pathRoleDelete,
			},
		},

		HelpSynopsis:    pathRoleHelpSyn,
		HelpDescription: pathRoleHelpDesc,
	}
}

func (b *backend) pathRoleWrite(ctx context.Context, req *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	roleName := d.Get("role").(string)
	if roleName == "" {
		return logical.ErrorResponse("missing role name"), nil
	}

	// Allowed users is an optional field, applicable for both OTP and CA types.
	allowedUsers := d.Get("allowed_users").(string)

	// Validate the CIDR blocks
	cidrList := d.Get("cidr_list").(string)
	if cidrList != "" {
		valid, err := cidrutil.ValidateCIDRListString(cidrList, ",")
		if err != nil {
			return nil, fmt.Errorf("failed to validate cidr_list: %w", err)
		}
		if !valid {
			return logical.ErrorResponse("failed to validate cidr_list"), nil
		}
	}

	// Validate the excluded CIDR blocks
	excludeCidrList := d.Get("exclude_cidr_list").(string)
	if excludeCidrList != "" {
		valid, err := cidrutil.ValidateCIDRListString(excludeCidrList, ",")
		if err != nil {
			return nil, fmt.Errorf("failed to validate exclude_cidr_list entry: %w", err)
		}
		if !valid {
			return logical.ErrorResponse("failed to validate exclude_cidr_list entry: %v", err), nil
		}
	}

	port := d.Get("port").(int)
	if port == 0 {
		port = 22
	}

	keyType := d.Get("key_type").(string)
	if keyType == "" {
		return logical.ErrorResponse("missing key type"), nil
	}
	keyType = strings.ToLower(keyType)

	var roleEntry sshRole
	switch keyType {
	case KeyTypeOTP:
		defaultUser := d.Get("default_user").(string)
		if defaultUser == "" {
			return logical.ErrorResponse("missing default user"), nil
		}

		// Below are the only fields used from the role structure for OTP type.
		roleEntry = sshRole{
			DefaultUser:     defaultUser,
			CIDRList:        cidrList,
			ExcludeCIDRList: excludeCidrList,
			KeyType:         KeyTypeOTP,
			Port:            port,
			AllowedUsers:    allowedUsers,
			Version:         roleEntryVersion,
		}
	case KeyTypeDynamic:
		return logical.ErrorResponse("dynamic key type roles are no longer supported"), nil
	case KeyTypeCA:
		algorithmSigner := DefaultAlgorithmSigner
		algorithmSignerRaw, ok := d.GetOk("algorithm_signer")
		if ok {
			algorithmSigner = algorithmSignerRaw.(string)
			switch algorithmSigner {
			case ssh.KeyAlgoRSA, ssh.KeyAlgoRSASHA256, ssh.KeyAlgoRSASHA512:
			case "", DefaultAlgorithmSigner:
				// This case is valid, and the sign operation will use the signer's
				// default algorithm. Explicitly reset the value to the default value
				// rather than use the more vague implicit empty string.
				algorithmSigner = DefaultAlgorithmSigner
			default:
				return nil, fmt.Errorf("unknown algorithm signer %q", algorithmSigner)
			}
		}

		role, errorResponse := b.createCARole(allowedUsers, d.Get("default_user").(string), algorithmSigner, d)
		if errorResponse != nil {
			return errorResponse, nil
		}
		roleEntry = *role
	default:
		return logical.ErrorResponse("invalid key type"), nil
	}

	entry, err := logical.StorageEntryJSON(fmt.Sprintf("roles/%s", roleName), roleEntry)
	if err != nil {
		return nil, err
	}

	if err := req.Storage.Put(ctx, entry); err != nil {
		return nil, err
	}
	return nil, nil
}

func (b *backend) createCARole(allowedUsers, defaultUser, signer string, data *framework.FieldData) (*sshRole, *logical.Response) {
	ttl := time.Duration(data.Get("ttl").(int)) * time.Second
	maxTTL := time.Duration(data.Get("max_ttl").(int)) * time.Second
	role := &sshRole{
		AllowedCriticalOptions:    data.Get("allowed_critical_options").(string),
		AllowedExtensions:         data.Get("allowed_extensions").(string),
		AllowUserCertificates:     data.Get("allow_user_certificates").(bool),
		AllowHostCertificates:     data.Get("allow_host_certificates").(bool),
		AllowedUsers:              allowedUsers,
		AllowedUsersTemplate:      data.Get("allowed_users_template").(bool),
		AllowedDomains:            data.Get("allowed_domains").(string),
		AllowedDomainsTemplate:    data.Get("allowed_domains_template").(bool),
		DefaultUser:               defaultUser,
		DefaultUserTemplate:       data.Get("default_user_template").(bool),
		AllowBareDomains:          data.Get("allow_bare_domains").(bool),
		AllowSubdomains:           data.Get("allow_subdomains").(bool),
		AllowUserKeyIDs:           data.Get("allow_user_key_ids").(bool),
		AllowEmptyPrincipals:      data.Get("allow_empty_principals").(bool),
		DefaultExtensionsTemplate: data.Get("default_extensions_template").(bool),
		KeyIDFormat:               data.Get("key_id_format").(string),
		KeyType:                   KeyTypeCA,
		AlgorithmSigner:           signer,
		Version:                   roleEntryVersion,
		NotBeforeDuration:         time.Duration(data.Get("not_before_duration").(int)) * time.Second,
		Issuer:                    data.Get("issuer_ref").(string),
	}

	if !role.AllowUserCertificates && !role.AllowHostCertificates {
		return nil, logical.ErrorResponse("Either 'allow_user_certificates' or 'allow_host_certificates' must be set to 'true'")
	}

	defaultCriticalOptions := convertMapToStringValue(data.Get("default_critical_options").(map[string]interface{}))
	defaultExtensions := convertMapToStringValue(data.Get("default_extensions").(map[string]interface{}))
	allowedUserKeyLengths, err := convertMapToIntSlice(data.Get("allowed_user_key_lengths").(map[string]interface{}))
	if err != nil {
		return nil, logical.ErrorResponse("error processing allowed_user_key_lengths: %s", err.Error())
	}

	if ttl != 0 && maxTTL != 0 && ttl > maxTTL {
		return nil, logical.ErrorResponse(
			`"ttl" value must be less than "max_ttl" when both are specified`,
		)
	}

	// Persist TTLs
	role.TTL = ttl.String()
	role.MaxTTL = maxTTL.String()
	role.DefaultCriticalOptions = defaultCriticalOptions
	role.DefaultExtensions = defaultExtensions
	role.AllowedUserKeyTypesLengths = allowedUserKeyLengths

	// Just like in PKI, we ensure that the issuers ref is set to an non-empty value,
	// 'default' if not set, and do not resolve the reference at role creation time;
	// Instead, resolving it at use time.
	if len(role.Issuer) == 0 {
		role.Issuer = defaultRef
	}

	return role, nil
}

func (b *backend) getRole(ctx context.Context, s logical.Storage, n string) (*sshRole, error) {
	entry, err := s.Get(ctx, "roles/"+n)
	if err != nil {
		return nil, err
	}
	if entry == nil {
		return nil, nil
	}

	var result sshRole
	if err := entry.DecodeJSON(&result); err != nil {
		return nil, err
	}

	if err := b.checkUpgrade(ctx, s, n, &result); err != nil {
		return nil, err
	}

	return &result, nil
}

func (b *backend) checkUpgrade(ctx context.Context, s logical.Storage, n string, result *sshRole) error {
	modified := false

	// NOTE: When introducing a new migration, increment roleEntryVersion and
	// check if the version is less than the version this change was introduced
	// at and perform the change. At the end, set modified and update the
	// version to the version this migration was introduced at! Additionally,
	// add new migrations after all existing migrations.
	//
	// Otherwise, past or future migrations may not execute!
	if result.Version == roleEntryVersion {
		return nil
	}

	// Role version introduced at version 1, migrating OldAllowedUserKeyLengths
	// to the newer AllowedUserKeyTypesLengths field.
	if result.Version < 1 {
		// Only migrate if we have old data and no new data to avoid clobbering.
		//
		// This change introduced the first role version, value of 1.
		if len(result.OldAllowedUserKeyLengths) > 0 && len(result.AllowedUserKeyTypesLengths) == 0 {
			result.AllowedUserKeyTypesLengths = make(map[string][]int)
			for k, v := range result.OldAllowedUserKeyLengths {
				result.AllowedUserKeyTypesLengths[k] = []int{v}
			}
			result.OldAllowedUserKeyLengths = nil
		}

		result.Version = 1
		modified = true
	}

	// Role version 2 migrates an empty AlgorithmSigner to an explicit ssh-rsa
	// value WHEN the SSH CA key is a RSA key.
	if result.Version < 2 {
		// In order to perform the version 2 upgrade, we need knowledge of the
		// signing key type as we want to make ssh-rsa an explicitly notated
		// algorithm choice.
		var publicKey ssh.PublicKey
		publicKeyEntry, err := caKey(ctx, s, caPublicKey)
		if err != nil {
			b.Logger().Debug(fmt.Sprintf("failed to load public key entry while attempting to migrate: %v", err))
			goto SKIPVERSION2
		}
		if publicKeyEntry == nil || publicKeyEntry.Key == "" {
			b.Logger().Debug("got empty public key entry while attempting to migrate")
			goto SKIPVERSION2
		}

		publicKey, err = parsePublicSSHKey(publicKeyEntry.Key)
		if err == nil {
			// Move an empty signing algorithm to an explicit ssh-rsa (SHA-1)
			// if this key is of type RSA. This isn't a secure default but
			// exists for backwards compatibility with existing versions of
			// Vault. By making it explicit, operators can see that this is
			// the value and move it to a newer algorithm in the future.
			if publicKey.Type() == ssh.KeyAlgoRSA && result.AlgorithmSigner == "" {
				result.AlgorithmSigner = ssh.KeyAlgoRSA
			}

			result.Version = 2
			modified = true
		}

	SKIPVERSION2:
		err = nil //nolint:ineffassign // we explicitly ignore the error
	}

	if result.Version < 3 {
		modified = true
		result.NotBeforeDuration = 30 * time.Second
		result.Version = 3
	}

	if result.Version < 4 {
		modified = true
		result.Issuer = defaultRef
		result.Version = 4
	}

	// Add new migrations just before here.
	//
	// Condition copied from PKI builtin.
	if modified && (b.System().LocalMount() || !b.System().ReplicationState().HasState(consts.ReplicationPerformanceSecondary)) {
		jsonEntry, err := logical.StorageEntryJSON("roles/"+n, &result)
		if err != nil {
			return err
		}
		if err := s.Put(ctx, jsonEntry); err != nil {
			// Only perform upgrades on replication primary
			if !strings.Contains(err.Error(), logical.ErrReadOnly.Error()) {
				return err
			}
		}
	}

	return nil
}

// parseRole converts a sshRole object into its map[string]interface representation,
// with appropriate values for each KeyType. If the KeyType is invalid, it will return
// an error.
func (b *backend) parseRole(role *sshRole) (map[string]interface{}, error) {
	var result map[string]interface{}

	switch role.KeyType {
	case KeyTypeOTP:
		result = map[string]interface{}{
			"default_user":      role.DefaultUser,
			"cidr_list":         role.CIDRList,
			"exclude_cidr_list": role.ExcludeCIDRList,
			"key_type":          role.KeyType,
			"port":              role.Port,
			"allowed_users":     role.AllowedUsers,
		}
	case KeyTypeCA:
		ttl, err := parseutil.ParseDurationSecond(role.TTL)
		if err != nil {
			return nil, err
		}
		maxTTL, err := parseutil.ParseDurationSecond(role.MaxTTL)
		if err != nil {
			return nil, err
		}

		result = map[string]interface{}{
			"allowed_users":               role.AllowedUsers,
			"allowed_users_template":      role.AllowedUsersTemplate,
			"allowed_domains":             role.AllowedDomains,
			"allowed_domains_template":    role.AllowedDomainsTemplate,
			"default_user":                role.DefaultUser,
			"default_user_template":       role.DefaultUserTemplate,
			"ttl":                         int64(ttl.Seconds()),
			"max_ttl":                     int64(maxTTL.Seconds()),
			"allowed_critical_options":    role.AllowedCriticalOptions,
			"allowed_extensions":          role.AllowedExtensions,
			"allow_user_certificates":     role.AllowUserCertificates,
			"allow_host_certificates":     role.AllowHostCertificates,
			"allow_bare_domains":          role.AllowBareDomains,
			"allow_subdomains":            role.AllowSubdomains,
			"allow_user_key_ids":          role.AllowUserKeyIDs,
			"allow_empty_principals":      role.AllowEmptyPrincipals,
			"key_id_format":               role.KeyIDFormat,
			"key_type":                    role.KeyType,
			"default_critical_options":    role.DefaultCriticalOptions,
			"default_extensions":          role.DefaultExtensions,
			"default_extensions_template": role.DefaultExtensionsTemplate,
			"allowed_user_key_lengths":    role.AllowedUserKeyTypesLengths,
			"algorithm_signer":            role.AlgorithmSigner,
			"not_before_duration":         int64(role.NotBeforeDuration.Seconds()),
			"issuer_ref":                  role.Issuer,
		}
	case KeyTypeDynamic:
		return nil, errors.New("dynamic key type roles are no longer supported")
	default:
		return nil, fmt.Errorf("invalid key type: %v", role.KeyType)
	}

	return result, nil
}

func (b *backend) pathRoleList(ctx context.Context, req *logical.Request, data *framework.FieldData) (*logical.Response, error) {
	txRollback, err := logical.StartTxStorage(ctx, req)
	if err != nil {
		return nil, err
	}
	defer txRollback()

	after := data.Get("after").(string)
	limit := data.Get("limit").(int)
	if limit <= 0 {
		limit = -1
	}

	entries, err := req.Storage.ListPage(ctx, "roles/", after, limit)
	if err != nil {
		return nil, err
	}

	keyInfo := map[string]interface{}{}
	for _, entry := range entries {
		role, err := b.getRole(ctx, req.Storage, entry)
		if err != nil {
			// On error, log warning and continue
			b.Logger().Warn("error getting role info", "role", entry, "error", err)
			continue
		}
		if role == nil {
			// On empty role, log warning and continue
			b.Logger().Warn("no role info found", "role", entry)
			continue
		}

		roleInfo, err := b.parseRole(role)
		if err != nil {
			b.Logger().Warn("error parsing role info", "role", entry, "error", err)
			continue
		}

		entryInfo := map[string]interface{}{}
		if keyType, ok := roleInfo["key_type"]; ok {
			entryInfo["key_type"] = keyType
		}

		if issuerRef, ok := roleInfo["issuer_ref"]; ok {
			entryInfo["issuer_ref"] = issuerRef
		}

		if len(entryInfo) != 0 {
			keyInfo[entry] = entryInfo
		}
	}

	if err := logical.EndTxStorage(ctx, req); err != nil {
		return nil, err
	}

	return logical.ListResponseWithInfo(entries, keyInfo), nil
}

func (b *backend) pathRoleRead(ctx context.Context, req *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	role, err := b.getRole(ctx, req.Storage, d.Get("role").(string))
	if err != nil {
		return nil, err
	}
	if role == nil {
		return nil, nil
	}

	roleInfo, err := b.parseRole(role)
	if err != nil {
		return nil, err
	}

	return &logical.Response{
		Data: roleInfo,
	}, nil
}

func (b *backend) pathRoleDelete(ctx context.Context, req *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	txRollback, err := logical.StartTxStorage(ctx, req)
	if err != nil {
		return nil, err
	}
	defer txRollback()

	roleName := d.Get("role").(string)

	// If the role was given privilege to accept any IP address, there will
	// be an entry for this role in zero-address roles list. Before the role
	// is removed, the entry in the list has to be removed.
	if err := b.removeZeroAddressRole(ctx, req.Storage, roleName); err != nil {
		return nil, err
	}

	if err := req.Storage.Delete(ctx, fmt.Sprintf("roles/%s", roleName)); err != nil {
		return nil, err
	}

	if err := logical.EndTxStorage(ctx, req); err != nil {
		return nil, err
	}

	return nil, nil
}

const pathRoleHelpSyn = `
Manage the 'roles' that can be created with this backend.
`

const pathRoleHelpDesc = `
This path allows you to manage the roles that are used to generate credentials.

Role takes a 'key_type' parameter that decides what type of credential this role
can generate. If remote hosts have OpenBao SSH Agent installed, an 'otp' type can
be used, otherwise 'dynamic' type can be used.

If the backend is mounted at "ssh" and the role is created at "ssh/roles/web",
then a user could request for a credential at "ssh/creds/web" for an IP that
belongs to the role. The credential will be for the 'default_user' registered
with the role. There is also an optional parameter 'username' for 'creds/' endpoint.
`

```

### changelog/3401.txt
[new file in patch, binary, or unreadable in pre-patch tree]

### sdk/framework/identity.go
```
// Copyright (c) HashiCorp, Inc.
// SPDX-License-Identifier: MPL-2.0

package framework

import (
	"errors"
	"fmt"

	"github.com/openbao/openbao/sdk/v2/helper/identitytpl"
	"github.com/openbao/openbao/sdk/v2/logical"
)

// PopulateIdentityTemplate takes a template string, an entity ID, and an
// instance of system view. It will query system view for information about the
// entity and use the resulting identity information to populate the template
// string.
func PopulateIdentityTemplate(tpl string, entityID string, sysView logical.SystemView) (string, error) {
	entity, err := sysView.EntityInfo(entityID)
	if err != nil {
		return "", err
	}
	if entity == nil {
		return "", errors.New("no entity found")
	}

	groups, err := sysView.GroupsForEntity(entityID)
	if err != nil {
		return "", err
	}

	input := identitytpl.PopulateStringInput{
		String: tpl,
		Entity: entity,
		Groups: groups,
		Mode:   identitytpl.ACLTemplating,
	}

	_, out, err := identitytpl.PopulateString(input)
	if err != nil {
		return "", err
	}

	return out, nil
}

// ValidateIdentityTemplate takes a template string and returns if the string is
// a valid identity template.
func ValidateIdentityTemplate(tpl string) (bool, error) {
	hasTemplating, _, err := identitytpl.PopulateString(identitytpl.PopulateStringInput{
		Mode:              identitytpl.ACLTemplating,
		ValidityCheckOnly: true,
		String:            tpl,
	})
	if err != nil {
		return false, fmt.Errorf("failed to validate policy templating: %w", err)
	}

	return hasTemplating, nil
}

```

### sdk/helper/identitytpl/templating.go
```
// Copyright (c) HashiCorp, Inc.
// SPDX-License-Identifier: MPL-2.0

package identitytpl

import (
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/hashicorp/go-secure-stdlib/parseutil"
	"github.com/openbao/openbao/sdk/v2/logical"
)

var (
	ErrUnbalancedTemplatingCharacter = errors.New("unbalanced templating characters")
	ErrNoEntityAttachedToToken       = errors.New("string contains entity template directives but no entity was provided")
	ErrNoGroupsAttachedToToken       = errors.New("string contains groups template directives but no groups were provided")
	ErrTemplateValueNotFound         = errors.New("no value could be found for one of the template directives")
)

const (
	ACLTemplating = iota // must be the first value for backwards compatibility
	JSONTemplating
)

type PopulateStringInput struct {
	String            string
	ValidityCheckOnly bool
	Entity            *logical.Entity
	Groups            []*logical.Group
	NamespaceID       string
	Mode              int       // processing mode, ACLTemplate or JSONTemplating
	Now               time.Time // optional, defaults to current time

	templateHandler templateHandlerFunc
	groupIDs        []string
	groupNames      []string
}

// templateHandlerFunc allows generating string outputs based on data type, and
// different handlers can be used based on mode. For example in ACL mode, strings
// are emitted verbatim, but they're wrapped in double quotes for JSON mode. And
// some structures, like slices, might be rendered in one mode but prohibited in
// another.
type templateHandlerFunc func(interface{}, ...string) (string, error)

// aclTemplateHandler processes known parameter data types when operating
// in ACL mode.
func aclTemplateHandler(v interface{}, keys ...string) (string, error) {
	switch t := v.(type) {
	case string:
		if t == "" {
			return "", ErrTemplateValueNotFound
		}
		return t, nil
	case []string:
		return "", ErrTemplateValueNotFound
	case map[string]string:
		if len(keys) > 0 {
			val, ok := t[keys[0]]
			if ok {
				return val, nil
			}
		}
		return "", ErrTemplateValueNotFound
	}

	return "", fmt.Errorf("unknown type: %T", v)
}

// jsonTemplateHandler processes known parameter data types when operating
// in JSON mode.
func jsonTemplateHandler(v interface{}, keys ...string) (string, error) {
	jsonMarshaller := func(v interface{}) (string, error) {
		enc, err := json.Marshal(v)
		if err != nil {
			return "", err
		}
		return string(enc), nil
	}

	switch t := v.(type) {
	case string:
		return strconv.Quote(t), nil
	case []string:
		return jsonMarshaller(t)
	case map[string]string:
		if len(keys) > 0 {
			return strconv.Quote(t[keys[0]]), nil
		}
		if t == nil {
			return "{}", nil
		}
		return jsonMarshaller(t)
	}

	return "", fmt.Errorf("unknown type: %T", v)
}

func PopulateString(p PopulateStringInput) (bool, string, error) {
	if p.String == "" {
		return false, "", nil
	}

	// preprocess groups
	for _, g := range p.Groups {
		p.groupNames = append(p.groupNames, g.Name)
		p.groupIDs = append(p.groupIDs, g.ID)
	}

	// set up mode-specific handler
	switch p.Mode {
	case ACLTemplating:
		p.templateHandler = aclTemplateHandler
	case JSONTemplating:
		p.templateHandler = jsonTemplateHandler
	default:
		return false, "", fmt.Errorf("unknown mode %q", p.Mode)
	}

	var subst bool
	splitStr := strings.Split(p.String, "{{")

	if len(splitStr) >= 1 {
		if strings.Contains(splitStr[0], "}}") {
			return false, "", ErrUnbalancedTemplatingCharacter
		}
		if len(splitStr) == 1 {
			return false, p.String, nil
		}
	}

	var b strings.Builder
	if !p.ValidityCheckOnly {
		b.Grow(2 * len(p.String))
	}

	for i, str := range splitStr {
		if i == 0 {
			if !p.ValidityCheckOnly {
				b.WriteString(str)
			}
			continue
		}
		splitPiece := strings.Split(str, "}}")
		switch len(splitPiece) {
		case 2:
			subst = true
			if !p.ValidityCheckOnly {
				tmplStr, err := performTemplating(strings.TrimSpace(splitPiece[0]), &p)
				if err != nil {
					return false, "", err
				}
				b.WriteString(tmplStr)
				b.WriteString(splitPiece[1])
			}
		default:
			return false, "", ErrUnbalancedTemplatingCharacter
		}
	}

	return subst, b.String(), nil
}

func performTemplating(input string, p *PopulateStringInput) (string, error) {
	performAliasTemplating := func(trimmed string, alias *logical.Alias) (string, error) {
		switch {
		case trimmed == "id":
			return p.templateHandler(alias.ID)

		case trimmed == "name":
			return p.templateHandler(alias.Name)

		case trimmed == "metadata":
			return p.templateHandler(alias.Metadata)

		case strings.HasPrefix(trimmed, "metadata."):
			split := strings.SplitN(trimmed, ".", 2)
			return p.templateHandler(alias.Metadata, split[1])

		case trimmed == "custom_metadata":
			return p.templateHandler(alias.CustomMetadata)

		case strings.HasPrefix(trimmed, "custom_metadata."):

			split := strings.SplitN(trimmed, ".", 2)
			return p.templateHandler(alias.CustomMetadata, split[1])

		}

		return "", ErrTemplateValueNotFound
	}

	performEntityTemplating := func(trimmed string) (string, error) {
		switch {
		case trimmed == "id":
			return p.templateHandler(p.Entity.ID)

		case trimmed == "name":
			return p.templateHandler(p.Entity.Name)

		case trimmed == "metadata":
			return p.templateHandler(p.Entity.Metadata)

		case strings.HasPrefix(trimmed, "metadata."):
			split := strings.SplitN(trimmed, ".", 2)
			return p.templateHandler(p.Entity.Metadata, split[1])

		case trimmed == "groups.names":
			return p.templateHandler(p.groupNames)

		case trimmed == "groups.ids":
			return p.templateHandler(p.groupIDs)

		case strings.HasPrefix(trimmed, "aliases."):
			split := strings.SplitN(strings.TrimPrefix(trimmed, "aliases."), ".", 2)
			if len(split) != 2 {
				return "", errors.New("invalid alias selector")
			}
			var alias *logical.Alias
			for _, a := range p.Entity.Aliases {
				if split[0] == a.MountAccessor {
					alias = a
					break
				}
			}
			if alias == nil {
				if p.Mode == ACLTemplating {
					return "", errors.New("alias not found")
				}

				// An empty alias is sufficient for generating defaults
				alias = &logical.Alias{Metadata: make(map[string]string), CustomMetadata: make(map[string]string)}
			}
			return performAliasTemplating(split[1], alias)
		}

		return "", ErrTemplateValueNotFound
	}

	performGroupsTemplating := func(trimmed string) (string, error) {
		var ids bool

		selectorSplit := strings.SplitN(trimmed, ".", 2)

		switch {
		case len(selectorSplit) != 2:
			return "", errors.New("invalid groups selector")

		case selectorSplit[0] == "ids":
			ids = true

		case selectorSplit[0] == "names":

		default:
			return "", errors.New("invalid groups selector")
		}
		trimmed = selectorSplit[1]

		accessorSplit := strings.SplitN(trimmed, ".", 2)
		if len(accessorSplit) != 2 {
			return "", errors.New("invalid groups accessor")
		}
		var found *logical.Group
		for _, group := range p.Groups {
			var compare string
			if ids {
				compare = group.ID
			} else {
				if p.NamespaceID != "" && group.NamespaceID != p.NamespaceID {
					continue
				}
				compare = group.Name
			}

			if compare == accessorSplit[0] {
				found = group
				break
			}
		}

		if found == nil {
			return "", fmt.Errorf("entity is not a member of group %q", accessorSplit[0])
		}

		trimmed = accessorSplit[1]

		switch {
		case trimmed == "id":
			return found.ID, nil

		case trimmed == "name":
			if found.Name == "" {
				return "", ErrTemplateValueNotFound
			}
			return found.Name, nil

		case strings.HasPrefix(trimmed, "metadata."):
			val, ok := found.Metadata[strings.TrimPrefix(trimmed, "metadata.")]
			if !ok {
				return "", ErrTemplateValueNotFound
			}
			return val, nil
		}

		return "", ErrTemplateValueNotFound
	}

	performTimeTemplating := func(trimmed string) (string, error) {
		now := p.Now
		if now.IsZero() {
			now = time.Now()
		}

		opsSplit := strings.SplitN(trimmed, ".", 3)

		if opsSplit[0] != "now" {
			return "", fmt.Errorf("invalid time selector %q", opsSplit[0])
		}

		result := now
		switch len(opsSplit) {
		case 1:
			// return current time
		case 2:
			return "", errors.New("missing time operand")

		case 3:
			duration, err := parseutil.ParseDurationSecond(opsSplit[2])
			if err != nil {
				return "", fmt.Errorf("invalid duration: %w", err)
			}

			switch opsSplit[1] {
			case "plus":
				result = result.Add(duration)
			case "minus":
				result = result.Add(-duration)
			default:
				return "", fmt.Errorf("invalid time operator %q", opsSplit[1])
			}
		}

		return strconv.FormatInt(result.Unix(), 10), nil
	}

	switch {
	case strings.HasPrefix(input, "identity.entity."):
		if p.Entity == nil {
			return "", ErrNoEntityAttachedToToken
		}
		return performEntityTemplating(strings.TrimPrefix(input, "identity.entity."))

	case strings.HasPrefix(input, "identity.groups."):
		if len(p.Groups) == 0 {
			return "", ErrNoGroupsAttachedToToken
		}
		return performGroupsTemplating(strings.TrimPrefix(input, "identity.groups."))

	case strings.HasPrefix(input, "time."):
		return performTimeTemplating(strings.TrimPrefix(input, "time."))
	}

	return "", ErrTemplateValueNotFound
}

```

### vault/logical_system.go
```
// Copyright (c) HashiCorp, Inc.
// SPDX-License-Identifier: MPL-2.0

package vault

import (
	"context"
	"crypto/sha256"
	"crypto/sha3"
	"crypto/sha512"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"hash"
	"maps"
	"math/rand"
	"net/http"
	"path"
	"path/filepath"
	"slices"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode"

	"github.com/go-viper/mapstructure/v2"
	"github.com/hashicorp/errwrap"
	log "github.com/hashicorp/go-hclog"
	"github.com/hashicorp/go-multierror"
	"github.com/hashicorp/go-secure-stdlib/parseutil"
	semver "github.com/hashicorp/go-version"
	"github.com/openbao/openbao/helper/hostutil"
	"github.com/openbao/openbao/helper/identity"
	"github.com/openbao/openbao/helper/logging"
	"github.com/openbao/openbao/helper/metricsutil"
	"github.com/openbao/openbao/helper/monitor"
	"github.com/openbao/openbao/helper/namespace"
	"github.com/openbao/openbao/helper/random"
	"github.com/openbao/openbao/helper/versions"
	"github.com/openbao/openbao/sdk/v2/framework"
	"github.com/openbao/openbao/sdk/v2/helper/consts"
	"github.com/openbao/openbao/sdk/v2/helper/jsonutil"
	"github.com/openbao/openbao/sdk/v2/helper/pluginutil"
	"github.com/openbao/openbao/sdk/v2/helper/wrapping"
	"github.com/openbao/openbao/sdk/v2/logical"
	"github.com/openbao/openbao/vault/policy"
	"github.com/openbao/openbao/vault/routing"
	"github.com/openbao/openbao/version"
)

const maxBytes = 128 * 1024

func NewSystemBackend(core *Core, logger log.Logger) *SystemBackend {
	b := &SystemBackend{
		Core:   core,
		logger: logger,
	}

	b.Backend = &framework.Backend{
		RunningVersion: versions.DefaultBuiltinVersion,
		Help:           strings.TrimSpace(sysHelpRoot),

		PathsSpecial: &logical.Paths{
			Root: []string{
				"auth/*",
				"remount",
				"audit",
				"audit/*",
				"raw",
				"raw/*",
				"rotate",
				"rotate/keyring",
				"rotate/root",
				"config/cors",
				"config/auditing/*",
				"config/ui/headers/*",
				"plugins/catalog/*",
				"revoke-prefix/*",
				"revoke-force/*",
				"leases/revoke-prefix/*",
				"leases/revoke-force/*",
				"leases/lookup/*",
				"leases",
				"internal/inspect/*",
			},

			Unauthenticated: []string{
				"wrapping/lookup",
				"wrapping/pubkey",
				"replication/status",
				"internal/specs/openapi",
				"internal/ui/mounts",
				"internal/ui/mounts/*",
				"internal/ui/namespaces",
				"storage/raft/bootstrap/challenge",
				"storage/raft/bootstrap/answer",
				"init",
				"seal-status",
				"unseal",
				"leader",
				"health",
				"decode-token",
				"mfa/validate",

				// These endpoints are unauthenticated only with the
				// "disable_unauthed_rekey_endpoints" listener property explicitly
				// set to false. Note that they are not routable through the normal
				// SystemBackend calls but are instead specially handled by http.
				"rekey/init",
				"rekey/update",
				"rekey/verify",
				"rekey-recovery-key/init",
				"rekey-recovery-key/update",
				"rekey-recovery-key/verify",

				// These endpoints are unauthenticated only with the
				// "disable_unauthed_generate_root_endpoints" listener property explicitly
				// set to false. Note that they are not routable through the normal
				// SystemBackend calls but are instead specially handled by http.
				"generate-root/attempt",
				"generate-root/update",
			},

			LocalStorage: []string{
				expirationSubPath,
				countersSubPath,
			},
		},
	}

	b.Paths = append(b.Paths, b.configPaths()...)
	b.Paths = append(b.Paths, b.rekeyPaths()...)
	b.Paths = append(b.Paths, b.rotatePaths()...)
	b.Paths = append(b.Paths, b.generateRootPaths()...)
	b.Paths = append(b.Paths, b.sealPaths()...)
	b.Paths = append(b.Paths, b.statusPaths()...)
	b.Paths = append(b.Paths, b.pluginsCatalogListPaths()...)
	b.Paths = append(b.Paths, b.pluginsCatalogCRUDPath())
	b.Paths = append(b.Paths, b.pluginsReloadPath())
	b.Paths = append(b.Paths, b.auditPaths()...)
	b.Paths = append(b.Paths, b.mountPaths()...)
	b.Paths = append(b.Paths, b.authPaths()...)
	b.Paths = append(b.Paths, b.lockedUserPaths()...)
	b.Paths = append(b.Paths, b.leasePaths()...)
	b.Paths = append(b.Paths, b.policyPaths()...)
	b.Paths = append(b.Paths, b.namespaceSealPaths()...)
	b.Paths = append(b.Paths, b.namespacePaths()...)
	b.Paths = append(b.Paths, b.wrappingPaths()...)
	b.Paths = append(b.Paths, b.toolsPaths()...)
	b.Paths = append(b.Paths, b.capabilitiesPaths()...)
	b.Paths = append(b.Paths, b.internalPaths()...)
	b.Paths = append(b.Paths, b.pprofPaths()...)
	b.Paths = append(b.Paths, b.remountPaths()...)
	b.Paths = append(b.Paths, b.metricsPath())
	b.Paths = append(b.Paths, b.monitorPath())
	b.Paths = append(b.Paths, b.inFlightRequestPath())
	b.Paths = append(b.Paths, b.hostInfoPath())
	b.Paths = append(b.Paths, b.quotasPaths()...)
	b.Paths = append(b.Paths, b.loginMFAPaths()...)
	b.Paths = append(b.Paths, b.introspectionPaths()...)
	b.Paths = append(b.Paths, b.workflowPaths()...)

	if core.rawEnabled {
		b.Paths = append(b.Paths, b.rawPaths()...)
	}
	if backend := core.GetRaftBackend(); backend != nil {
		b.Paths = append(b.Paths, b.raftStoragePaths()...)
	}

	return b
}

func (b *SystemBackend) rawPaths() []*framework.Path {
	r := &RawBackend{
		core:   b.Core,
		logger: b.logger,
	}
	return r.rawPaths("")
}

// SystemBackend implements logical.Backend and is used to interact with
// the core of the system. This backend is hardcoded to exist at the "sys"
// prefix. Conceptually it is similar to procfs on Linux.
type SystemBackend struct {
	*framework.Backend
	Core   *Core
	logger log.Logger
}

// handleConfigStateSanitized returns the current configuration state. The configuration
// data that it returns is a sanitized version of the combined configuration
// file(s) provided.
func (b *SystemBackend) handleConfigStateSanitized(ctx context.Context, req *logical.Request, data *framework.FieldData) (*logical.Response, error) {
	return &logical.Response{
		Data: b.Core.SanitizedConfig(),
	}, nil
}

// handleConfigReload handles reloading specific pieces of the configuration.
func (b *SystemBackend) handleConfigReload(ctx context.Context, req *logical.Request, data *framework.FieldData) (*logical.Response, error) {
	return nil, logical.ErrUnsupportedPath
}

// handleCORSRead returns the current CORS configuration
func (b *SystemBackend) handleCORSRead(ctx context.Context, req *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	corsConf := b.Core.corsConfig

	enabled := corsConf.IsEnabled()
	resp := &logical.Response{
		Data: map[string]interface{}{
			"enabled": enabled,
		},
	}

	if enabled {
		corsConf.RLock()
		resp.Data["allowed_origins"] = corsConf.AllowedOrigins
		resp.Data["allowed_headers"] = corsConf.AllowedHeaders
		resp.Data["allow_credentials"] = corsConf.AllowCredentials
		corsConf.RUnlock()
	}

	return resp, nil
}

// handleCORSUpdate sets the list of origins that are allowed to make
// cross-origin requests and sets the CORS enabled flag to true
func (b *SystemBackend) handleCORSUpdate(ctx context.Context, req *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	origins := d.Get("allowed_origins").([]string)
	headers := d.Get("allowed_headers").([]string)
	allow_credentials := d.Get("allow_credentials").(bool)

	return nil, b.Core.corsConfig.Enable(ctx, origins, headers, allow_credentials)
}

// handleCORSDelete sets the CORS enabled flag to false and clears the list of
// allowed origins & headers.
func (b *SystemBackend) handleCORSDelete(ctx context.Context, req *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	return nil, b.Core.corsConfig.Disable(ctx)
}

func (b *SystemBackend) handleTidyLeases(ctx context.Context, req *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	ns, err := namespace.FromContext(ctx)
	if err != nil {
		return nil, err
	}

	go func() {
		tidyCtx := namespace.ContextWithNamespace(b.Core.activeContext.Load(), ns)
		err := b.Core.expiration.Tidy(tidyCtx)
		if err != nil {
			b.Backend.Logger().Error("failed to tidy leases", "error", err)
			return
		}
	}()

	resp := &logical.Response{}
	resp.AddWarning("Tidy operation successfully started. Any information from the operation will be printed to OpenBao's server logs.")
	return logical.RespondWithStatusCode(resp, req, http.StatusAccepted)
}

func (b *SystemBackend) handleLeaseCount(ctx context.Context, req *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	typeRaw, ok := d.GetOk("type")
	if !ok || strings.ToLower(typeRaw.(string)) != "irrevocable" {
		return nil, nil
	}

	includeChildNamespacesRaw, ok := d.GetOk("include_child_namespaces")
	includeChildNamespaces := ok && includeChildNamespacesRaw.(bool)

	resp, err := b.Core.expiration.getIrrevocableLeaseCounts(ctx, includeChildNamespaces)
	if err != nil {
		return nil, err
	}

	return &logical.Response{
		Data: resp,
	}, nil
}

func processLimit(d *framework.FieldData) (bool, int, error) {
	limitStr := ""
	limitRaw, ok := d.GetOk("limit")
	if ok {
		limitStr = limitRaw.(string)
	}

	includeAll := false
	maxResults := MaxIrrevocableLeasesToReturn
	if limitStr == "" {
		// use the defaults
	} else if strings.ToLower(limitStr) == "none" {
		includeAll = true
	} else {
		// not having a valid, positive int here is an error
		limit, err := strconv.Atoi(limitStr)
		if err != nil {
			return false, 0, fmt.Errorf("invalid 'limit' provided: %w", err)
		}

		if limit < 1 {
			return false, 0, errors.New("limit must be 'none' or a positive integer")
		}

		maxResults = limit
	}

	return includeAll, maxResults, nil
}

func (b *SystemBackend) handleLeaseList(ctx context.Context, req *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	typeRaw, ok := d.GetOk("type")
	if !ok || strings.ToLower(typeRaw.(string)) != "irrevocable" {
		return nil, nil
	}

	includeChildNamespacesRaw, ok := d.GetOk("include_child_namespaces")
	includeChildNamespaces := ok && includeChildNamespacesRaw.(bool)

	includeAll, maxResults, err := processLimit(d)
	if err != nil {
		return nil, err
	}

	leases, warning, err := b.Core.expiration.listIrrevocableLeases(ctx, includeChildNamespaces, includeAll, maxResults)
	if err != nil {
		return nil, err
	}

	resp := &logical.Response{
		Data: leases,
	}
	if warning != "" {
		resp.AddWarning(warning)
	}

	return resp, nil
}

func (b *SystemBackend) handlePluginCatalogTypedList(ctx context.Context, req *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	pluginType, err := consts.ParsePluginType(d.Get("type").(string))
	if err != nil {
		return nil, err
	}

	plugins, err := b.Core.pluginCatalog.ListVersionedPlugins(ctx, pluginType)
	if err != nil {
		return nil, err
	}

	return logical.ListResponse(uniquePluginNames(plugins)), nil
}

func (b *SystemBackend) handlePluginCatalogUntypedList(ctx context.Context, _ *logical.Request, _ *framework.FieldData) (*logical.Response, error) {
	data := make(map[string]any)
	var versionedPlugins []pluginutil.VersionedPlugin
	for _, pluginType := range pluginTypes {
		plugins, err := b.Core.pluginCatalog.ListVersionedPlugins(ctx, pluginType)
		if err != nil {
			return nil, err
		}

		// Sort for consistent ordering
		sortVersionedPlugins(plugins)

		if len(plugins) > 0 {
			data[pluginType.String()] = uniquePluginNames(plugins)
		}

		versionedPlugins = append(versionedPlugins, plugins...)
	}

	if len(versionedPlugins) != 0 {
		// Audit logging uses reflection to HMAC the values of all fields in the
		// response recursively, which panics if it comes across any unexported
		// fields. Therefore, we have to rebuild the VersionedPlugin struct as
		// a map of primitive types to avoid the panic that would happen when
		// audit logging tries to HMAC the contents of the SemanticVersion field.
		var detailed []map[string]any
		for _, p := range versionedPlugins {
			entry := map[string]any{
				"type":    p.Type,
				"name":    p.Name,
				"version": p.Version,
				"builtin": p.Builtin,
			}
			if p.SHA256 != "" {
				entry["sha256"] = p.SHA256
			}
			if p.DeprecationStatus != "" {
				entry["deprecation_status"] = p.DeprecationStatus
			}
			detailed = append(detailed, entry)
		}
		data["detailed"] = detailed
	}

	return &logical.Response{
		Data: data,
	}, nil
}

func uniquePluginNames(plugins []pluginutil.VersionedPlugin) []string {
	pluginNames := make([]string, 0, len(plugins))

	for _, plugin := range plugins {
		index, match := slices.BinarySearch(pluginNames, plugin.Name)
		if match {
			continue
		}
		pluginNames = slices.Insert(pluginNames, index, plugin.Name)
	}

	return pluginNames
}

func sortVersionedPlugins(versionedPlugins []pluginutil.VersionedPlugin) {
	sort.SliceStable(versionedPlugins, func(i, j int) bool {
		left, right := versionedPlugins[i], versionedPlugins[j]
		if left.Type != right.Type {
			return left.Type < right.Type
		}
		if left.Name != right.Name {
			return left.Name < right.Name
		}
		if left.Version != right.Version {
			return right.SemanticVersion.GreaterThan(left.SemanticVersion)
		}

		return false
	})
}

func (b *SystemBackend) handlePluginCatalogUpdate(ctx context.Context, _ *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	pluginName := d.Get("name").(string)
	if pluginName == "" {
		return logical.ErrorResponse("missing plugin name"), nil
	}

	pluginTypeStr := d.Get("type").(string)
	if pluginTypeStr == "" {
		// If the plugin type is not provided, list it as unknown so that we
		// add it to the catalog and UpdatePlugins later will sort it.
		pluginTypeStr = "unknown"
	}
	pluginType, err := consts.ParsePluginType(pluginTypeStr)
	if err != nil {
		return nil, err
	}

	pluginVersion, builtin, err := getVersion(d)
	if err != nil {
		return logical.ErrorResponse(err.Error()), nil
	}
	if builtin {
		return logical.ErrorResponse("version %q is not allowed because 'builtin' is a reserved metadata identifier", pluginVersion), nil
	}

	sha256 := d.Get("sha256").(string)
	if sha256 == "" {
		sha256 = d.Get("sha_256").(string)
		if sha256 == "" {
			return logical.ErrorResponse("missing SHA-256 value"), nil
		}
	}

	command := d.Get("command").(string)
	if command == "" {
		return logical.ErrorResponse("missing command value"), nil
	}

	if err = b.Core.CheckPluginPerms(command); err != nil {
		return nil, err
	}

	oci := d.Get("oci").(bool)

	// For backwards compatibility, also accept args as part of command. Don't
	// accepts args in both command and args.
	args := d.Get("args").([]string)
	parts := strings.Split(command, " ")
	if len(parts) <= 0 {
		return logical.ErrorResponse("missing command value"), nil
	} else if len(parts) > 1 && len(args) > 0 {
		return logical.ErrorResponse("must not specify args in command and args field"), nil
	} else if len(parts) > 1 {
		args = parts[1:]
	}

	env := d.Get("env").([]string)

	sha256Bytes, err := hex.DecodeString(sha256)
	if err != nil {
		return logical.ErrorResponse("Could not decode SHA-256 value from Hex"), err
	}

	err = b.Core.pluginCatalog.Set(ctx, pluginName, pluginType, pluginVersion, parts[0], args, env, sha256Bytes, oci)
	if err != nil {
		if errors.Is(err, ErrPluginNotFound) || strings.HasPrefix(err.Error(), "plugin version mismatch") {
			return logical.ErrorResponse(err.Error()), nil
		}
		return nil, err
	}

	return nil, nil
}

func (b *SystemBackend) handlePluginCatalogRead(ctx context.Context, _ *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	pluginName := d.Get("name").(string)
	if pluginName == "" {
		return logical.ErrorResponse("missing plugin name"), nil
	}

	pluginTypeStr := d.Get("type").(string)
	if pluginTypeStr == "" {
		// If the plugin type is not provided (i.e. the old
		// sys/plugins/catalog/:name endpoint is being requested) short-circuit here
		// and return a warning
		resp := &logical.Response{}
		resp.AddWarning(fmt.Sprintf("Deprecated API endpoint, cannot read plugin information from catalog for %q", pluginName))
		return resp, nil
	}

	pluginType, err := consts.ParsePluginType(pluginTypeStr)
	if err != nil {
		return nil, err
	}

	pluginVersion, _, err := getVersion(d)
	if err != nil {
		return logical.ErrorResponse(err.Error()), nil
	}

	plugin, err := b.Core.pluginCatalog.Get(ctx, pluginName, pluginType, pluginVersion)
	if err != nil {
		return nil, err
	}
	if plugin == nil {
		return nil, nil
	}

	command := ""
	if !plugin.Builtin {
		command, err = filepath.Rel(b.Core.pluginCatalog.directory, plugin.Command)
		if err != nil {
			return nil, err
		}
	}

	data := map[string]interface{}{
		"name":        plugin.Name,
		"args":        plugin.Args,
		"command":     command,
		"sha256":      hex.EncodeToString(plugin.Sha256),
		"builtin":     plugin.Builtin,
		"version":     plugin.Version,
		"oci":         plugin.Oci,
		"declarative": plugin.Declarative,
	}

	if plugin.Builtin {
		status, _ := b.Core.builtinRegistry.DeprecationStatus(plugin.Name, plugin.Type)
		data["deprecation_status"] = status.String()
	}

	return &logical.Response{
		Data: data,
	}, nil
}

func (b *SystemBackend) handlePluginCatalogDelete(ctx context.Context, _ *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	pluginName := d.Get("name").(string)
	if pluginName == "" {
		return logical.ErrorResponse("missing plugin name"), nil
	}

	pluginVersion, builtin, err := getVersion(d)
	if err != nil {
		return logical.ErrorResponse(err.Error()), nil
	}
	if builtin {
		return logical.ErrorResponse("version %q cannot be deleted", pluginVersion), nil
	}

	var resp *logical.Response
	pluginTypeStr := d.Get("type").(string)
	if pluginTypeStr == "" {
		// If the plugin type is not provided (i.e. the old
		// sys/plugins/catalog/:name endpoint is being requested), set type to
		// unknown and let pluginCatalog.Delete proceed. It should handle
		// deregistering out of the old storage path (root of core/plugin-catalog)
		resp = new(logical.Response)
		resp.AddWarning(fmt.Sprintf("Deprecated API endpoint, cannot deregister plugin from catalog for %q", pluginName))
		pluginTypeStr = "unknown"
	}

	pluginType, err := consts.ParsePluginType(pluginTypeStr)
	if err != nil {
		return nil, err
	}
	if err := b.Core.pluginCatalog.Delete(ctx, pluginName, pluginType, pluginVersion); err != nil {
		return nil, err
	}

	return resp, nil
}

func getVersion(d *framework.FieldData) (version string, builtin bool, err error) {
	version = d.Get("version").(string)
	if version != "" {
		semanticVersion, err := semver.NewSemver(version)
		if err != nil {
			return "", false, fmt.Errorf("version %q is not a valid semantic version: %w", version, err)
		}

		// Canonicalize the version string.
		// Add the 'v' back in, since semantic version strips it out, and we want to be consistent with internal plugins.
		version = "v" + semanticVersion.String()
	}

	return version, versions.IsBuiltinVersion(version), nil
}

func (b *SystemBackend) handlePluginReloadUpdate(ctx context.Context, req *logical.Request, d *framework.FieldData) (*logical.Response, error) {
	pluginName := d.Get("plugin").(string)
	pluginMounts := d.Get("mounts").([]string)

	if pluginName != "" && len(pluginMounts) > 0 {
		return logical.ErrorResponse("plugin and mounts cannot be set at the same time"), nil
	}
	if pluginName == "" && len(pluginMounts) == 0 {
		return logical.ErrorResponse("plugin or mounts must be provided"), nil
	}

	if pluginName != "" {
		err := b.Core.reloadMatchingPlugin(ctx, pluginName)
		if err != nil {
			return handleError(err)
		}
	} else if len(pluginMounts) > 0 {
		err :
... [truncated, file is 171616 chars]
```

### vault/logical_system_paths.go
[omitted: context budget exhausted]

### vault/policy/policy.go
[omitted: context budget exhausted]

### vault/policy/policy_store.go
[omitted: context budget exhausted]

### website/content/api-docs/secret/pki.mdx
[omitted: context budget exhausted]

### website/content/api-docs/secret/ssh.mdx
[omitted: context budget exhausted]

### website/content/api-docs/system/policy.mdx
[omitted: context budget exhausted]
Callers & Entry Points (How public input reaches the modified code)
(none)
Repository Map
ui/  (6 files)
ui/app/  (620 files)
ui/config/  (3 files)
ui/lib/  (297 files)
ui/mirage/  (27 files)
ui/scripts/  (11 files)
ui/tests/  (392 files)
ui/types/  (25 files)
website/  (4 files)
website/content/  (3 files)
website/src/  (11 files)
... (1399 source files in total)
Package Manifests (Dependencies, scripts, build configuration)
### go.mod
```
module github.com/openbao/openbao

// The go version directive value isn't consulted when building our production binaries,
// and the vault module isn't intended to be imported into other projects.  As such the
// impact of this setting is usually rather limited.  Note however that in some cases the
// Go project introduces new semantics for handling of go.mod depending on the value.
//
// The general policy for updating it is: when the Go major version used on the branch is
// updated. If we choose not to do so at some point (e.g. because we don't want some new
// semantic related to Go module handling), this comment should be updated to explain that.

go 1.25.8

replace github.com/openbao/openbao/api/v2 => ./api

replace github.com/openbao/openbao/api/auth/approle/v2 => ./api/auth/approle

replace github.com/openbao/openbao/api/auth/kubernetes/v2 => ./api/auth/kubernetes

replace github.com/openbao/openbao/api/auth/userpass/v2 => ./api/auth/userpass

replace github.com/openbao/openbao/sdk/v2 => ./sdk

replace github.com/boltdb/bolt => ./helper/stubbolt

require (
	cloud.google.com/go/monitoring v1.29.0
	github.com/ProtonMail/go-crypto v1.4.1
	github.com/armon/go-radix v1.0.0
	github.com/caddyserver/certmagic v0.25.4
	github.com/cenkalti/backoff/v5 v5.0.3
	github.com/containerd/platforms v0.2.1
	github.com/coreos/go-systemd/v22 v22.6.0
	github.com/duosecurity/duo_api_golang v0.2.0
	github.com/evanphx/json-patch/v5 v5.9.11
	github.com/fatih/color v1.19.0
	github.com/go-jose/go-jose/v4 v4.1.4
	github.com/go-ldap/ldap/v3 v3.4.13
	github.com/go-ldap/ldif v0.0.0-20200320164324-fd88d9b715b3
	github.com/go-sql-driver/mysql v1.10.0
	github.com/go-test/deep v1.1.1
	github.com/go-viper/mapstructure/v2 v2.5.0
	github.com/gocql/gocql v1.7.0
	github.com/golang-jwt/jwt/v4 v4.5.2
	github.com/google/cel-go v0.28.1
	github.com/google/go-containerregistry v0.21.7
	github.com/google/go-metrics-stackdriver v0.2.0
	github.com/hashicorp/cap v0.13.0
	github.com/hashicorp/cli v1.1.7
	github.com/hashicorp/errwrap v1.1.0
	github.com/hashicorp/go-cleanhttp v0.5.2
	github.com/hashicorp/go-discover v1.3.0
	github.com/hashicorp/go-hclog v1.6.3
	github.com/hashicorp/go-memdb v1.3.5
	github.com/hashicorp/go-metrics v0.6.0
	github.com/hashicorp/go-msgpack v0.5.5
	github.com/hashicorp/go-multierror v1.1.1
	github.com/hashicorp/go-plugin v1.8.0
	github.com/hashicorp/go-raftchunking v0.7.1
	github.com/hashicorp/go-retryablehttp v0.7.8
	github.com/hashicorp/go-secure-stdlib/base62 v0.1.2
	github.com/hashicorp/go-secure-stdlib/fileutil v0.1.0
	github.com/hashicorp/go-secure-stdlib/kv-builder v0.1.2
	github.com/hashicorp/go-secure-stdlib/nonceutil v0.1.0
	github.com/hashicorp/go-secure-stdlib/parseutil v0.2.0
	github.com/hashicorp/go-secure-stdlib/password v0.1.5
	github.com/hashicorp/go-secure-stdlib/reloadutil v0.1.1
	github.com/hashicorp/go-secure-stdlib/strutil v0.1.2
	github.com/hashicorp/go-secure-stdlib/tlsutil v0.1.3
	github.com/hashicorp/go-sockaddr v1.0.7
	github.com/hashicorp/go-syslog v1.0.0
	github.com/hashicorp/go-uuid v1.0.3
	github.com/hashicorp/go-version v1.9.0
	github.com/hashicorp/golang-lru/v2 v2.0.7
	github.com/hashicorp/hcl v1.0.1-vault-7
	github.com/hashicorp/hcl/v2 v2.24.0
	github.com/hashicorp/raft v1.7.3
	github.com/hashicorp/raft-autopilot v0.3.0
	github.com/hashicorp/raft-boltdb/v2 v2.3.1
	github.com/influxdata/influxdb1-client v0.0.0-20200827194710-b269163b24ab
	github.com/jackc/pgx/v5 v5.10.0
	github.com/jcmturner/gokrb5/v8 v8.4.4
	github.com/jefferai/isbadcipher v0.0.0-20190226160619-51d2077c035f
	github.com/klauspost/compress v1.18.7
	github.com/kr/pretty v0.3.1
	github.com/kr/text v0.2.0
	github.com/mattn/go-colorable v0.1.15
	github.com/mattn/go-isatty v0.0.22
	github.com/mediocregopher/radix/v4 v4.1.5
	github.com/mholt/acmez/v3 v3.1.6
	github.com/michaelklishin/rabbit-hole/v3 v3.5.0
	github.com/mitchellh/copystructure v1.2.0
	github.com/mitchellh/go-testing-interface v1.14.2-0.20210821155943-2d9075ca8770
	github.com/mitchellh/go-wordwrap v1.0.1
	github.com/mitchellh/pointerstructure v1.2.1
	github.com/mitchellh/reflectwalk v1.0.2
	github.com/moby/moby/api v1.55.0
	github.com/moby/moby/client v0.5.0
	github.com/oklog/run v1.2.0
	github.com/okta/okta-sdk-golang/v2 v2.20.0
	github.com/openbao/go-kms-wrapping/plugin/v2 v2.3.0
	github.com/openbao/go-kms-wrapping/v2 v2.8.0
	github.com/openbao/go-kms-wrapping/wrappers/kmip/v2 v2.2.0
	github.com/openbao/go-kms-wrapping/wrappers/static/v2 v2.2.0
	github.com/openbao/go-kms-wrapping/wrappers/transit/v2 v2.8.0
	github.com/openbao/openbao-template v1.0.1
	github.com/openbao/openbao/api/auth/approle/v2 v2.0.0
	github.com/openbao/openbao/api/auth/userpass/v2 v2.0.0
	github.com/openbao/openbao/api/v2 v2.6.0
	github.com/openbao/openbao/sdk/v2 v2.6.0
	github.com/ory/dockertest/v4 v4.0.0
	github.com/pires/go-proxyproto v0.12.0
	github.com/posener/complete v1.2.3
	github.com/pquerna/otp v1.5.0
	github.com/prometheus/client_golang v1.23.2
	github.com/prometheus/common v0.69.0
	github.com/rboyer/safeio v0.2.3
	github.com/ryanuber/columnize v2.1.2+incompatible
	github.com/ryanuber/go-glob v1.0.0
	github.com/sasha-s/go-deadlock v0.3.9
	github.com/sethvargo/go-limiter v1.1.0
	github.com/shirou/gopsutil/v4 v4.26.6
	github.com/stretchr/testify v1.11.1
	github.com/tink-crypto/tink-go/v2 v2.7.0
	github.com/tsaarni/certyaml v0.11.0
	github.com/yeqown/go-qrcode/v2 v2.2.5
	go.etcd.io/bbolt v1.5.0
	go.opentelemetry.io/otel v1.44.0
	go.opentelemetry.io/otel/sdk v1.44.0
	go.opentelemetry.io/otel/trace v1.44.0
	go.uber.org/zap v1.28.0
	golang.org/x/crypto v0.53.0
	golang.org/x/exp v0.0.0-20260112195511-716be5621a96
	golang.org/x/net v0.56.0
	golang.org/x/oauth2 v0.36.0
	golang.org/x/sync v0.21.0
	golang.org/x/sys v0.46.0
	golang.org/x/term v0.44.0
	golang.org/x/text v0.38.0
	google.golang.org/api v0.286.0
	google.golang.org/grpc v1.81.1
	google.golang.org/protobuf v1.36.11
	gopkg.in/jcmturner/goidentity.v3 v3.0.0
	k8s.io/api v0.35.4
	k8s.io/apimachinery v0.35.4
	k8s.io/clie
```
Context & Existing Test Patterns
Existing test files touched by the patch: builtin/logical/pki/backend_test.go, builtin/logical/ssh/backend_test.go, http/sys_policy_test.go, sdk/helper/identitytpl/templating_test.go, vault/external_tests/policy/acl_templating_test.go, vault/logical_system_test.go
Repository top-level entries: .github, .gitignore, .go-version, .golangci.deprecations.yml, .golangci.yml, .hooks, .release, AGENTS.md, CHANGELOG.md, CHARTER.md, CLAUDE.md, CNAME, CODEOWNERS, CONTRIBUTING.md, Dockerfile, GOVERNANCE.md, LICENSE, MAINTAINERS.md, Makefile, README.md, api, audit, builtin, changelog, command, go.mod, go.sum, goreleaser.linux.yaml, goreleaser.other.yaml, helper, http, main.go, physical, plugins, publiccode.yml, scripts, sdk, serviceregistration, tools, ui, vault, version, website
Project's own test patterns and conventions:
### vault/dynamic_system_view_test.go
```
// Copyright (c) HashiCorp, Inc.
// SPDX-License-Identifier: MPL-2.0

package vault

import (
	"context"
	"encoding/base64"
	"fmt"
	"reflect"
	"sort"
	"testing"
	"time"

	log "github.com/hashicorp/go-hclog"
	ldapcred "github.com/openbao/openbao/builtin/credential/ldap"
	"github.com/openbao/openbao/helper/namespace"
	"github.com/openbao/openbao/sdk/v2/framework"
	"github.com/openbao/openbao/sdk/v2/logical"
	"github.com/stretchr/testify/require"
)

var (
	testPolicyName        = "testpolicy"
	rawTestPasswordPolicy = `
length = 20
rule "charset" {
	charset = "abcdefghijklmnopqrstuvwxyz"
	min_chars = 1
}
rule "charset" {
	charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	min_chars = 1
}
rule "charset" {
	charset = "0123456789"
	min_chars = 1
}`
	rawTestPasswordPolicy2 = `
length = 10
rule "charset" {
	charset = "abcdefghijklmnopqrstuvwxyz"
	min_chars = 1
}`
)

func TestIdentity_BackendTemplating(t *testing.T) {
	var err error
	coreConfig := &CoreConfig{
		DisableCache: true,
		Logger:       log.NewNullLogger(),
		CredentialBackends: map[string]logical.Factory{
			"ldap": ldapcred.Factory,
		},
	}

	cluster := NewTestCluster(t, coreConfig, &TestClusterOptions{})

	cluster.Start()
	defer cluster.Cleanup()

	core := cluster.Cores[0].Core

	TestWaitActive(t, core)

	req := logical.TestRequest(t, logical.UpdateOperation, "sys/auth/ldap")
	req.ClientToken = cluster.RootToken
	req.Data["type"] = "ldap"
	resp, err := core.HandleRequest(namespace.RootContext(t.Context()), req)
	if err != nil {
		t.Fatalf("err: %v", err)
	}
	if resp != nil {
		t.Fatalf("bad: %v", resp)
	}

	req = logical.TestRequest(t, logical.ReadOperation, "sys/auth")
	req.ClientToken = cluster.RootToken
	resp, err = core.HandleRequest(namespace.RootContext(t.Context()), req)
	if err != nil {
		t.Fatalf("err: %v", err)
	}

	accessor := resp.Data["ldap/"].(map[string]interface{})["accessor"].(string)

	// Create an entity
	req = logical.TestRequest(t, logical.UpdateOperation, "identity/entity")
	req.ClientToken = cluster.RootToken
	req.Data["name"] = "entity1"
	req.Data["metadata"] = map[string]string{
		"organization": "hashicorp",
		"team":         "vault",
	}
	resp, err = core.HandleRequest(namespace.RootContext(t.Context()), req)
	if err != nil {
		t.Fatal(err)
	}

	entityID := resp.Data["id"].(string)

	// Create an alias
	req = logical.TestRequest(t, logical.UpdateOperation, "identity/entity-alias")
	req.ClientToken = cluster.RootToken
	req.Data["name"] = "alias1"
	req.Data["canonical_id"] = entityID
	req.Data["mount_accessor"] = accessor
	resp, err = core.HandleRequest(namespace.RootContext(t.Context()), req)
	if err != nil {
		t.Fatal(err)
	}

	aliasID := resp.Data["id"].(string)

	// Create a group
	req = logical.TestRequest(t, logical.UpdateOperation, "identity/group")
	req.ClientToken = cluster.RootToken
	req.Data["name"] = "group1"
	req.Data["member_entity_ids"] = []string{entityID}
	req.Data["metadata"] = map[string]string{
		"group": "vault",
	}
	resp, err = core.HandleRequest(namespace.RootContext(t.Context()), req)
	if err != nil {
		t.Fatal(err)
	}

	groupID := resp.Data["id"].(string)

	// Get the ldap mount
	sysView := core.router.MatchingSystemView(namespace.RootContext(t.Context()), "auth/ldap/")

	tCases := []struct {
		tpl      string
		expected string
	}{
		{
			tpl:      "{{identity.entity.id}}",
			expected: entityID,
		},
		{
			tpl:      "{{identity.entity.name}}",
			expected: "entity1",
		},
		{
			tpl:      "{{identity.entity.metadata.organization}}",
			expected: "hashicorp",
		},
		{
			tpl:      "{{identity.entity.aliases." + accessor + ".id}}",
			expected: aliasID,
		},
		{
			tpl:      "{{identity.entity.aliases." + accessor + ".name}}",
			expected: "alias1",
		},
		{
			tpl:      "{{identity.groups.ids." + groupID + ".name}}",
			expected: "group1",
		},
		{
			tpl:      "{{identity.groups.names.group1.id}}",
			expected: groupID,
		},
		{
			tpl:      "{{identity.groups.names.group1.metadata.group}}",
			expected: "vault",
		},
		{
			tpl:      "{{identity.groups.ids." + groupID + ".metadata.group}}",
			expected: "vault",
		},
	}

	for _, tCase := range tCases {
		out, err := framework.PopulateIdentityTemplate(tCase.tpl, entityID, sysView)
		if err != nil {
			t.Fatal(err)
		}

		if out != tCase.expected {
			t.Fatalf("got %q, expected %q", out, tCase.expected)
		}
	}
}

func TestDynamicSystemView_GeneratePasswordFromPolicy_successful(t *testing.T) {
	var err error
	coreConfig := &CoreConfig{
		DisableCache:       true,
		Logger:             log.NewNullLogger(),
		CredentialBackends: map[string]logical.Factory{},
	}

	cluster := NewTestCluster(t, coreConfig, &TestClusterOptions{})

	cluster.Start()
	defer cluster.Cleanup()

	core := cluster.Cores[0].Core
	TestWaitActive(t, core)

	b64Policy := base64.StdEncoding.EncodeToString([]byte(rawTestPasswordPolicy))

	path := fmt.Sprintf("sys/policies/password/%s", testPolicyName)
	req := logical.TestRequest(t, logical.CreateOperation, path)
	req.ClientToken = cluster.RootToken
	req.Data["policy"] = b64Policy

	_, err = core.HandleRequest(namespace.RootContext(t.Context()), req)
	if err != nil {
		t.Fatalf("err: %v", err)
	}

	ctx, cancel := context.WithTimeout(t.Context(), 1*time.Second)
	defer cancel()

	ctx = namespace.RootContext(ctx)
	dsv := TestDynamicSystemView(cluster.Cores[0].Core, nil)

	runeset := map[rune]bool{}
	runesFound := []rune{}

	for range 100 {
		actual, err := dsv.GeneratePasswordFromPolicy(ctx, testPolicyName)
		if err != nil {
			t.Fatalf("no error expected, but got: %s", err)
		}
		for _, r := range actual {
			if runeset[r] {
				continue
			}
			runeset[r] = true
			runesFound = append(runesFound, r)
		}
	}

	sort.Sort(runes(runesFound))

	expectedRunes := []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
	sort.Sort(runes(expectedRunes)) // Sort it so they can be compared

	if !reflect.DeepEqual(runesFound, expectedRunes) {
		t.Fatalf("Didn't find all characters from the charset\nActual  : [%s]\nExpected: [%s]", string(runesFound), string(expectedRunes))
	}
}

func TestDynamicSystemView_GeneratePasswordFromPolicy_failed(t *testing.T) {
	type testCase struct {
		policyName string
		entry      *logical.StorageEntry
	}

	tests := map[string]testCase{
		"no policy name": {
			policyName: "",
		},
		"no policy found": {
			policyName: "testpolicy",
		},
		"error retrieving policy": {
			policyName: "testpolicy",
		},
		"saved policy is malformed": {
			policyName: "testpolicy",
			entry: &logical.StorageEntry{
				Key:   getPasswordPolicyKey("testpolicy"),
				Value: []byte(`{"policy":"asdfahsdfasdf"}`),
			},
		},
	}

	for name, test := range tests {
		t.Run(name, func(t *testing.T) {
			core, _, _ := TestCoreUnsealed(t)

			ctx, cancel := context.WithTimeout(t.Context(), 1*time.Second)
			defer cancel()

			if test.entry != nil {
				core.systemBarrierView.Put(ctx, test.entry)
			}

			dsv := TestDynamicSystemView(core, nil)

			actualPassword, err := dsv.GeneratePasswordFromPolicy(ctx, test.policyName)
			if err == nil {
				t.Fatal("err expected, got nil")
			}
			if actualPassword != "" {
				t.Fatalf("no password expected, got %s", actualPassword)
			}
		})
	}
}

func TestDynamicSystemView_GeneratePasswordFromPolicy_namespaces(t *testing.T) {
	core, _, token := TestCoreUnsealed(t)

	TestCoreCreateNamespaces(
		t, core,
		&namespace.Namespace{Path: "foo/"},
		&namespace.Namespace{Path: "foo/bar/"},
	)

	ctx := namespace.RootContext(t.Context())

	fooNs, err := core.namespaceStore.GetNamespaceByPath(ctx, "foo/")
	require.NoError(t, err)
	barNs, err := core.namespaceStore.GetNamespaceByPath(ctx, "foo/bar")
	require.NoError(t, err)

	// Create password policy in the 'foo/' namespace.
	path := fmt.Sprintf("sys/policies/password/%s", testPolicyName)
	req := logical.TestRequest(t, logical.CreateOperation, path)
	b64Policy := base64.StdEncoding.EncodeToString([]byte(rawTestPasswordPolicy))
	req.Data["policy"] = b64Policy
	req.ClientToken = token
	_, err = core.HandleRequest(namespace.ContextWithNamespace(ctx, fooNs), req)
	require.NoError(t, err)

	// Password policy should only work in the 'foo/' namespace,
	// not a child namespace, not the root namespace.
	pass, err := TestDynamicSystemView(core, fooNs).GeneratePasswordFromPolicy(ctx, testPolicyName)
	require.NoError(t, err)
	require.NotEmpty(t, pass)
	pass, err = TestDynamicSystemView(core, barNs).GeneratePasswordFromPolicy(ctx, testPolicyName)
	require.Error(t, err)
	require.Empty(t, pass)
	pass, err = TestDynamicSystemView(core, nil).GeneratePasswordFromPolicy(ctx, testPolicyName)
	require.Error(t, err)
	require.Empty(t, pass)

	// Create another password policy in the root namespace, with the same name.
	path = fmt.Sprintf("sys/policies/password/%s", testPolicyName)
	req = logical.TestRequest(t, logical.CreateOperation, path)
	b64Policy = base64.StdEncoding.EncodeToString([]byte(rawTestPasswordPolicy2))
	req.Data["policy"] = b64Policy
	req.ClientToken = token
	_, err = core.HandleRequest(ctx, req)
	require.NoError(t, err)

	// Password policy in 'foo/' should still act the same
	pass, err = TestDynamicSystemView(core, fooNs).GeneratePasswordFromPolicy(ctx, testPolicyName)
	require.NoError(t, err)
	require.NotEmpty(t, pass)
	require.Len(t, pass, 20)

	// Password policy in root namespace should now be available, but generate passwords
	// according to different constraints.
	pass, err = TestDynamicSystemView(core, nil).GeneratePasswordFromPolicy(ctx, testPolicyName)
	require.NoError(t, err)
	require.NotEmpty(t, pass)
	require.Len(t, pass, 10)
}

type runes []rune

func (r runes) Len() int           { return len(r) }
func (r runes) Less(i, j int) bool { return r[i] < r[j] }
func (r runes) Swap(i, j int)      { r[i], r[j] = r[j], r[i] }

```
Your Deliverables
Artifact 1: instruction.md - The Incident Defect Report
Write a realistic report (about 150-350 words) as a user or operator who hit the problem. Sections: a title naming
the symptom (not the fix); what was observed and how (the route the user hit); impact; what must keep working.

WHAT ACTUALLY DECIDES DIFFICULTY (measured, 2 accepted vs 37 solved): not how vague the report is, but whether part of
the root cause lives in a REAL place the report never leads to, with a test that reaches it. The accepted hono task's
report stated the cause and the rule, and listed three affected wrappers - both models still failed 6/6, because the
second renderer and the nested-array root were never mentioned and were tested. So the report may describe the
route(s) the user hit; its one job is to NOT reveal the hidden place(s) or how far the bug reaches.

NEVER (each measured on a task both models then solved; ids are the evidence):
- state the SCOPE or completeness of the bug: "the same acceptance happens on each one we tried", "for every operation",
  "on every route", "every command that ...", "all three nodes". It tells the agent to grep for every sibling and the
  trap disappears - oauth-providers fm3f, n8n f3f2, vitest p63j, q2xc (all four solved on attempt 1). Show the route(s)
  the user hit; whether others exist is for the agent to find;
- reveal or hint at a hidden place (metadata.trap.paths): not by name, and not by a role specific enough to find it;
- list the tainted parameters, the payload set or the variants your tests use (n8n f3f2 named all four tainted
  parameters and the legal operator list). One illustrative example of the symptom is fine;
- name a function by a behaviour so specific it identifies it ("the one that ignores the address's own suffix" - j6r3);
- offer or rule on an acceptable fix ("refusing the archive is fine" - p634) or say which layer should change;
- in "what must keep working", list the boundary VALUES your tests use ("/0 networks, IPv4-mapped addresses",
  "[db].[dbo].[t], numeric-string limits"). Name the FEATURES that must keep working (hono: "a bare string must still
  render as the top-level element", "content marked as trusted raw HTML still emits markup");
- file, directory, module, function, method or class names the fix changes, options it adds, or line numbers.
AVOID stating the root cause when the fix is in one local place: there it IS the answer (adm-zip p634: "two entries
with the same name"; ip-address j6r3: "never checks both sides are the same kind of address").
Write in your OWN words. Do not quote the official CVE/GHSA summary, and do not include the CVE/OSV ID.
Fairness: every test_functional_* exercises an ordinary use of a feature named under "what must keep working", and
every test_security_* is an instance of the harm described.
Artifact 2: hidden_tests.py - Black-Box Pytest Suite
The suite runs at the repository root with REPO_ROOT set.
Strict Constraints:
Pure pytest, deterministic, offline (no internet access, no sleeps > 1s, harmless sentinels/tmp_path only).
Black-Box Execution: Test ONLY via public entry points (public CLI commands, public API methods, exported library
functions, or HTTP route handlers). NEVER import, inspect, or call new helper functions, new structs, or new fields
introduced by the reference patch.
Agnostic Assertions: Accept ANY valid rejection mechanism (raised exception, HTTP 4xx, sanitized return value).
Never assert on exact error string text or specific internal exception classes added by the patch.
Language Adapters:
Python: Direct import of public pre-patch modules.
Node/TypeScript: Use subprocess to run project's test runner (vitest/jest) or inline node script driving src/ (NEVER dist/).
Go: Write temporary zz_hidden_<name>_test.go and execute via go test -count=1 ./<pkg>.
PHP (Composer): Write a temporary zz_hidden_<name>.php in the repo root starting with require __DIR__ . '/vendor/autoload.php';
drive the project's public API or HTTP kernel the way its own tests do, print ONE JSON line of what a caller observes, and
run it with php via subprocess (remove the file in a finally block). Use only classes that exist in the PRE-patch source;
never change composer.json/composer.lock; no database or network - use the project's in-memory/array/SQLite drivers.
Non-Destructive Invariant: The reference patch MUST score 100% (all tests pass). The vulnerable code MUST fail all
test_security_* tests.
Naming & Test Structure:
test_security_* (at least 3, ideally 4-8): Fail on vulnerable code, pass after a correct fix.
COVER EVERY FIX PLACE (the #1 measured cause of easy tasks: in 24 of 37 solved tasks the agent passed while changing
FEWER source files than the reference fix - e.g. 1 of 12 - because no test reached the other places). List every source
place the reference fix hardens; give EACH its own test_security_* reached through its OWN real entry point, so a
repair that skips any one place fails. A variant counts only if it reaches the root cause through a DIFFERENT place or
route. Spelling, case, whitespace, encoding or extension variants of the same input through the same route do NOT
count - measured: pure spelling/encoding variants are always caught, and input variants were never missed.
Strongest sibling kinds to target (measured miss rates): a mechanism that never had the protection so its absence
reads as design (32%); a producer - schema, serializer, loader, config resolver - that feeds the check through a path
the check never calls (29%); a second real implementation (fallback backend, adapter, inline copy) (19%); the check
authorising the wrong/neighbouring object or an attacker-chosen identity field; the restricted value arriving through
defaults, merge, inheritance or stored config. Prefer REAL siblings the upstream fix also changed or never touched.
test_functional_* (at least 3, ideally 4-8): Pass on both vulnerable and fixed code.
Legitimate inputs near the rejection boundary, custom enterprise configurations, and valid workflows. An over-broad
fix that disables features or universally rejects input must fail these tests.
Hard Rules Learned from Historical QA Rejections
THE FAIRNESS CONTRACT (NO UNSEEN PLUMBING): every test_functional_* must exercise an ordinary use of a FEATURE named
under "What must keep working" - name the feature, not the test's values. If a test needs private enterprise registries
(e.g. my-tfe.corp.example), the report says that "users who configure a private registry" must keep working; it does
not list hosts, env vars or edge cases. A feature the vulnerable code never supported is not "legitimate" (infracost).
SIBLING BLAST RADIUS (INCOMPLETE UPSTREAM FIXES): If the reference patch only fixes 7 out of 8 providers/parsers
(leaving sibling components vulnerable), and an intelligent agent fixing the 8th component would break pre-existing
repository tests (e.g., legacy tests asserting unauthenticated behavior for provider X), answer ONLY with:
<unsuitable>incomplete upstream fix: sibling provider tests break under full remediation</unsuitable>.
IMPLEMENTATION INDEPENDENCE: A test must pass for ANY reasonable, correct architecture. Never assert that a check
lives in a specific layer, or that internal state changed in a specific way, when an alternative placement is equally sound.
COMPILED REPOSITORIES (TS/GO): Test source code directly. Never require compiled bundles (dist/index.js) which
do not exist until build and would omit agent edits.
NO TRIVIAL OR SYNTHETIC CODE: If the vulnerability is a pure dependency bump, a config toggle, or does not support
a multi-file / deeper-layer trap, answer ONLY with: <unsuitable>no hidden-path trap: <reason></unsuitable>.
Artifact 3: check_patches - Three Validation Fixes
Provide search/replace edits on pre-patch source files to verify test suite discrimination:
"shallow": Quick band-aid fixing only the primary trigger. Must pass >= 1 security test, but FAIL >= 1 security variant.
"removal": Over-restrictive fix (disables feature/returns early). Must FAIL >= 1 functional test.
"alternative": A correct, clean fix designed differently than the reference patch. Must PASS ALL tests.
Output Format (Strict XML Blocks Only)
Return ONLY these four blocks, nothing else:
<instruction_md>
...markdown matching the exact section structure specified above...
</instruction_md>
<hidden_tests_py>
...python source, no code fences...
</hidden_tests_py>
<task_metadata_json>
{
"entry_point": "<public entry point string>",
"techniques": [1, 5, 9],
"trap": {
"paths": ["<repo-relative source file agent is likely to miss>"],
"contract": "<the specific legitimate behavior near the boundary that functional tests pin>"
},
"fix_places": ["<EVERY reference-fix source file whose change closes part of the vulnerability; the pipeline re-runs the fix
               WITHOUT each one and a test must then fail>"],
"unrelated_files": ["<every OTHER reference-fix source file (refactor, typing, logging, an unrelated feature bundled in the
                    commit). Every source file of the reference patch must appear in fix_places or here>"],
"test_justifications": {
"<test_function_name>": "<exact sentence or quote from instruction.md requiring this test's assertion>"
}
}
</task_metadata_json>
<check_patches_json>
{
"shallow": [{"file": "<path>", "search": "<exact existing code>", "replace": "<new code>"}],
"removal": [...],
"alternative": [...]
}
</check_patches_json>


# The checks your task will face (write it to pass all of them the first time)
An independent reviewer scores the task on these criteria; any failed "must pass" criterion sends it back:
- no_hints (must pass): instruction.md names no file, module, path, line number, or function/class the fix changes AND does not prescribe the fix: an 'expected behaviour' part may state the security property and the legitimate behaviour to keep, but must not describe validation rules, accepted token formats, ordering of checks, or logging-vs-returning choices that amount to the fix design
- accurate_report (must pass): the report describes the vulnerability the oracle patch actually fixes (impact + how it is triggered), without inventing a different flaw
- solvable_from_report (must pass): a skilled engineer who reads the report and the code could determine every behaviour the hidden tests require; no test demands undisclosed or arbitrary behaviour
- real_entry_point (must pass): security tests reach the bug through a real entry point (public API/route/CLI), not by calling the internal function the patch edits
- variants_share_root_cause (must pass): extra exploit variants share the root cause and are all blocked by the oracle patch (no extra hardening the oracle does not provide)
- implementation_agnostic (must pass): tests never import/assert anything the patch adds, never assert exact error text, and accept any reasonable way of blocking the attack
- functional_meaningful (must pass): functional tests would FAIL if the feature were removed, disabled or over-blocked, yet pass on the vulnerable code
- deterministic_offline (must pass): no network, no timing/sleep-based races, no randomness that can flip a result
- realistic (must pass): the scenario is a realistic use of the project, not a contrived snippet or unreachable code
- security_not_trivial_config (must pass): the vulnerability is in program logic, not a dependency bump or config toggle
Then the task is EXECUTED: the reference fix must score 1.0 twice; the vulnerable code must fail every test_security_*
and pass every test_functional_*; the repo's own related tests must pass before and after the fix; your three check
patches run against your tests (shallow must still fail a security test, removal must fail a functional test,
alternative must pass everything); and if both target models can name the fix location from your report alone, the
task is rejected (so describe behaviour, never location).


# Design contract (measured: tasks that break BOTH models satisfy these)
1. At least TWO independent public entry points reach the root cause. The report names at most one; the other is
   discoverable by reading the code (a second renderer/parser/implementation, a lower-level public constructor, a
   second HTTP route/CLI, or a save/reload round-trip). Give each entry point its own test_security_*.
2. At EACH entry point, test at least two input shapes (bare value vs array/nested; path vs bytes; casing or encoding
   variants). A fix that handles only the reported shape must still fail.
3. Put at least one affected sink in a module whose path/name does not suggest the vulnerability; the report must not
   name it.
4. Include a functional test for every "must keep working" clause: it must PASS on the PRE-patch code and FAIL if the
   feature is removed or over-blocked.
5. At least one security test must be blocked only by the fix's change in a SECOND source file, not by the obvious
   first file. If the whole fix is one shared choke point, the models will solve the task.


# Task-design techniques (curated - follow them)
## What counts as a model failure (the grading contract)
- A task is solved only by reward 1.0: every hidden security test, every hidden functional test and every enforced
  existing repo test passes. Anything less is a FAILURE, including:
  - **Partial fix:** the agent closes some attack paths but not all (e.g. 5 of 6 security variants blocked). This is the
    most valuable failure: the model was confident and wrong ("silent failure").
  - **Fix that breaks something:** the hole is closed but a legitimate behaviour, an existing repo test, or the build
    breaks (over-correction / regression).
  - Both at once.
- A task is ACCEPTED when every attempt of both models (3 + 3) is such a failure, and the deterministic checks prove
  each failure is the model's (graded, no API/harness crash, agent really worked, no tampering). No AI judge decides.
- The goal is to MEASURE repair quality: a task only an incomplete or over-broad repair fails is a good task.
- So every task must be designed so that (a) a partial fix still fails and (b) an over-broad fix still fails.
- **Measured: models fail in two ways, equally often.** In the 2 QA-verified ACCEPTED tasks, 6 of 12 failures
  were over-corrections (apprise: hole closed, a pinned interface broken) and 6 left a path open (hono: a second
  renderer / input shape). So spend as much design effort on legitimate use as on attacks: functional tests for
  every legitimate input shape next to each attack variant, a public interface the repo's own tests pin
  (technique 11), and existing behaviour the obvious
  fix would change (hono: nested-array roots; apprise: the plugin `meta` dict). A "must keep working" test must follow from the report and
  pass on any correct fix - never a design only the reference fix makes (fairness QA withdrew infracost GHSA-6x6c and
  oauth-providers GHSA-fm3f for exactly that).

## Pattern catalogue - evidence-ranked from 471 measured sibling traps (2026-10-20)
A task shows ONE symptom through ONE route (the base bug). A **sibling** is another place the same protection is
missing that the report never names; a fix of the reported site alone then scores < 1.0. Every trap has two axes.

### Origin - where the sibling comes from (this is what decides difficulty, more than the mechanism)
- **A-FAR** (Pattern A): a site the real upstream fix ALSO changed, which the report does not lead to. **19% missed.** KEEP.
- **B-ROUTE** (Pattern B): a real, unmodified route with the same gap the upstream fix never touched. **25% missed - the strongest.** KEEP.
- **INJ** (injected/planted by us): **5% missed - almost never bites.** Once a model accepts the concept it closes all
  planted routes together (124 of 166 injected siblings are just M1/M2 routes of the stated concept). **TOO EASY - do not
  rely on injected siblings as the difficulty.** Confirmed 2026-10-20: our filament injection was declared unsuitable by
  the trap gate itself - every planted surface passed through one query scoper, so one restoration closed them all.
- Non-sibling kinds: **BASE** (the reported site), **SHAPE TRAP** (pure spelling/encoding variant of a route - ALWAYS
  caught, TOO EASY), **COUPLED TRAP** (a must-keep-working legitimate value next to the hidden one, tested functionally -
  bites, esp. MiMo which over-hardens; DeepSeek breaks coupled values too).

### Mechanism - why a model skips the sibling (miss rate = missed in >=1 run / siblings with trial data)
TOP BREAKERS (design toward these, on REAL code = A-FAR or B-ROUTE):
- **M4 Feature-absent** - the mechanism never had the protection, so its absence reads as design ("unsupported combo, not
  a boundary"). **7/22 = 32%, highest.** e.g. jackson any-setter has no view code.
- **M6 Producer off the check's path** - a schema/serializer/loader/config-resolver feeds the check through a path the
  check never calls; the model follows calls INTO the check, never asks where its data comes from. **5/17 = 29%.**
- **M2 Second implementation** (real, not injected) - a duplicate copy of the guarded logic: another package, fallback
  backend, adapter, inline copy. **14/73 = 19%.** "That path uses its own helper / only a fallback."
- **M10 Wrong object** - authorises a neighbouring/proxy object, or trusts an attacker-chosen identity field. **2/11.**
- **M5 Merged/defaults route** - the restricted value arrives via defaults/merge/inheritance/patch/stored-config; the
  model treats the report's example fields as the whole set.
- **M11 Coupled contract** - a linked visible value or shared helper must keep working; the natural fix breaks it
  (over-broad-fix trap). Bites MiMo hard.
WEAK / TOO EASY (do not use as the sole difficulty):
- **M1 Parallel entry** - another handler/endpoint/tool reaches the same sink. Only **12/99 = 12%** on real code, and ~0
  when injected. Allowed only as a secondary trap stacked with a top breaker.
- **M8 Parser differential** - genuine canonicalisation mismatch bites rarely (1/18); **pure spelling/case/encoding is
  always caught - TOO EASY.**
- **M12 Input variants** (encoding/spelling/verb/protocol/role of a stated input) - **never missed. TOO EASY, remove.**
- **M3 Shared layer** (0/6) and **M9 Fail-open fallback** (0/9) - never observed to bite; not proven breakers.

### The winning recipe (the only both-model breaker, jackson-databind-sib2, audited)
Uses NO planted code. A **Pattern B** route that **stacks several DIFFERENT mechanisms**: M4 (any-setter ignores views) +
M10+M11 (object-id stand-in property) + M5 (array/merge update) + a **coupled visible value an over-broad fix breaks**.
So: pick a real uncovered route, give it 2-3 different mechanisms, and pin a coupled legitimate value functionally.

### Avoid the checklist tell
Model-built (-ds/-mm) reports don't name siblings but describe each sibling's surface in product terms, one clause per
trap - that hands the solver a map. Never enumerate the HIDDEN places. (hono's report listed three affected wrappers
and still broke both models - because the places that decided it, the second renderer and the nested-array root, were
not in the list. Describing the route the user hit is fine; describing where else it lives is not.)

---

## Legacy numbered techniques (still referenced by the generator gate and scoreboard; map to the catalogue above)
Mapping: 1->M1, 2->dismissal-reason, 3->M3, 4->grading, 5->M11/coupled, 6->leak discipline, 7->M2, 8->RETIRED (M12),
9->M11, 10->RETIRED (width), 11->M11, 12->M4, 13->M6, 14->M10, 15->M5. The generator's trap gate accepts 1, 2, 3, 7 and
12-15 as hidden-path techniques; prefer 12, 13 and a real (not injected) 7. M1 parallel entry alone is weak (12%).

## What makes a repair task demanding - so only a complete, careful repair passes (use several in ONE task)
1. **Unnamed sibling path.** The report describes the reported trigger only. The same root cause is reachable through
   a second entry point, a second code path, or a round-trip (serialize -> store -> parse) that the report never
   names. Give it its own security test. Evidence: DeepSeek missed the schema round-trip variant in 3/3 runs on 6qxp.
2. **Already-protected-looking code.** One path already validates correctly, so the model reads the area as "handled"
   and patches only the path the report mentions (pyload jq7h, 6qxp).
3. **Fix across a layer boundary.** The correct fix must reach from the entry layer into a deeper layer (e.g. a core
   API that cannot see the web session, an SDK helper that cannot see the stored binding). Local guards at the entry
   point are the shallow fix your tests must catch.
4. **One test per fix place.** Each place the reference fix hardens gets its own `test_security_*` reached through its
   own entry point, so a fix that skips one place still scores < 1.0. (Was "one test per variant"; spelling, case and
   encoding variants of one input through one route are always caught and do not count.)
5. **Boundary-hugging functional tests.** Legitimate inputs that look like the attack (same characters, same feature,
   trailing slash, empty/None, legacy unbound data) must keep working, so "reject everything suspicious" fails.
6. **Behavioural report, no localization, no scope.** Describe what a user observes ("an IPv6 client passed our IPv4
   allowlist"), never the function, class, file or the root cause wording that points at the line to change - and
   never how far the bug reaches ("each provider we tried", "on every route"): all 4 evaluated reports with such a
   phrase were solved on attempt 1. Stating the cause is fatal only for a one-place fix; hono stated it and still won.
7. **Parallel implementation.** The project has a second module that re-implements the same feature (a second
   renderer, a second parser, a legacy and a new API). The report describes the behaviour once; the fix must land in
   both. Evidence: hono GHSA-hxh3 (first ACCEPTED task) - in 4 of 6 attempts the second `jsx/dom/server` renderer was
   left unfixed (DeepSeek read it every time but argued a top-level string is "trusted HTML"; MiMo twice never looked);
   the other 2 fixed it for a bare string only and missed a nested-array root. Details: data/knowledge/failure_analyses/.
8. **Input-shape variants (RETIRED - do not use as a difficulty technique).** In 35 of 40 tagged tasks, break rate at
   the 15% baseline: models catch spelling, case, encoding and shape variants of one route. A second public API or
   lower-level constructor that is a REAL separate place is technique 1 or 7, not this one.
9. **A "must keep working" clause that argues against the fix.** DeepSeek uses such a clause (or an existing test that
   passes either way) as permission to leave a sink open; MiMo over-hardens and breaks the legitimate path - test the
   legitimate behaviour in every supported composition order (undici GHSA-vp8m).
10. **Prefer big fixes (RETIRED as a difficulty lever).** Width does not separate hard from easy: 10-21-file fixes
   were solved on attempt 1 (9router changed 1 of 12 fix files and scored 1.0). Tiny local fixes (<= 3 files, <= 35
   lines) are still unusable, so width is a floor, not a lever.
11. **A compatibility contract pinned by an existing repo test.** Pick fixes that add an option or a check next to
   an existing public interface that the project's own tests pin (the exact keys a plugin receives, an output format,
   a default). The obvious fix changes that interface; a careful fix keeps it. Evidence: apprise GHSA-856c
   (ACCEPTED) - in 6 of 6 attempts both models added the new `redirect` key to every plugin's parsed-URL dict "like
   `verify`", saw the repo test `len(meta) == 8` fail, and edited the test instead of their fix; the grader restores
   repo tests, so all 6 scored 0.99. The upstream fix kept the key out unless set. Make sure the existing test is in
   the enforced pass->pass set and the report does not tell the agent to change that interface.
12. **Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22).** A mechanism that never had the
   protection, so its absence reads as design ("unsupported combination, not a boundary"). jackson: the any-setter
   route has no view code at all. Test it through its own entry point.
13. **Producer off the check's path (M6, 5 of 17).** A schema, serializer, loader or config resolver feeds the check
   through a path the check never calls; the model follows calls INTO the check and never asks where its data comes
   from. MCP SDK 6qxp: the schema strips the issuer on reload (DeepSeek missed it 3/3).
14. **Wrong object (M10).** The check authorises a neighbouring or proxy object, or trusts an attacker-chosen identity
   field (seaweedfs: authorises against the ARN's account field; django-cms: parent from POST while the check reads GET).
15. **Merged / defaults route (M5).** The restricted value arrives through defaults, merge, inheritance, a patch or
   stored config; the model treats the report's example fields as the whole set (protobuf.js: inherited options).

## Cover every place the real fix protects (measured)
- In 15 of 27 solved tasks the agent passed while changing FEWER source files than the reference fix: the hidden tests
  did not exercise every place the fix protects, so a partial repair scored 1.0. Before writing tests, list each source
  file / code path the reference fix hardens and give each one at least one security test reached from a real entry
  point. A repair that skips any of those places must fail. (Live numbers: data/knowledge/solved_profile.md.)

## How the pipeline proves the tests are good (your check patches)
- **shallow**: blocks only the reported trigger. At least one security test must still fail on it (technique 1/4).
- **removal**: disables or over-restricts the feature. At least one functional test must fail on it (technique 5).
- **alternative**: a correct fix of a different design. Every test must pass on it (tests are implementation-agnostic).
- **coverage (leave-one-file-out)**: the reference fix is run WITHOUT its change to each file you list in
  `fix_places` (metadata). At least one test must fail every time; otherwise an agent that skips that file solves
  the task and it is sent back. List only files whose change closes part of the vulnerability.
- These are executed in the real environment. A wrong outcome sends the task back with the failing test names.

## Fairness rules (never break these to make a task harder)
- Every hidden test is passed by the reference fix and follows from the report plus a careful reading of the code.
- Tests observe only what a caller can observe at the entry point; never internal state or names the fix adds.
- No timing races, no network, no randomness.
- **Never test a number the report does not state.** The reference fix's internal limits (max length 64, a 1,000,000
  cap, a depth limit) are ONE design; another correct fix may pick another value. (Most common rejection so far:
  pypdf, source-map-js.) For resource-exhaustion bugs: keep the legitimate input small and the attack input orders of
  magnitude larger (e.g. 1x vs 1000x), and assert only that the attack is refused or finishes quickly and bounded -
  never at which exact size it starts being refused. If a boundary matters, the report must state it.
- **Variants must share the reported root cause.** Another bug in the same area (a different slow path, a different
  missing check) is a different task, not a variant (rejected: source-map-js deep nesting, typespec output files).
- **Never map every exception to "blocked".** Catch only the project's own rejection (UnauthorizedException, a 4xx,
  its ValidationError); let any other error fail the test. A catch-all hid a broken fake request in sync-in (the
  guard crashed on a missing `request.url`), so legitimate-use tests failed for no visible reason - and the same
  catch-all lets a security test "pass" when the code under test never ran.
- **"Must keep working" means it works today.** Every functional test must pass on the vulnerable code; never describe
  as legitimate a behaviour the project never had (rejected: undici allow-list caching).

## Answer-key hygiene (the agent must use its own knowledge)
- The agent sees only the report and the repo at the vulnerable commit: no hidden tests, no fix, no git history of
  the fix, no network, no advisory text. Never put fix code, upstream regression tests or exploit inputs into the repo
  or the report. Fixes committed after the models' release dates keep the answer out of their training data.


# Which task types each evaluated agent could not repair completely (measured results)
## Model failure map (deterministic, rebuilt after every evaluation)
Task type = vulnerability family; fix breadth (files / dirs / lines). Timeouts are not failures.
### DeepSeek
- FAILED on (5): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) - partial fix: closed 5 of 6 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: schema_roundtrip_keeps_binding | information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines) - partial fix: closed 4 of 5 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: toolbox_symlink_escape | auth / session / credentials; local fix (1 files / 1 dir / 33 lines) - partial fix: closed 6 of 7 attack variants in its run and stopped on its own (it thought it was done); left open every time: exp_at_epoch_boundary
- Timed out on (0): none
- Solved (35), by vulnerability family: resource exhaustion (DoS) x7, auth / session / credentials x7, other x6, path / file handling x3, parsing / type confusion x3, injection (code / command / markup) x2, injection (code / command / markup) + information exposure x1, parsing / type confusion + SSRF / redirect x1, information exposure x1, auth / session / credentials + injection (code / command / markup) x1, auth / session / credentials + path / file handling x1, deserialization / prototype pollution x1, auth / session / credentials + path / file handling + information exposure x1
### MiMo
- FAILED on (3): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines) - closed the hole but broke legitimate behaviour (storage_with_custom_lookup_same_host) in its run and stopped on its own (it thought it was done)
- Timed out on (2): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | auth / session / credentials; wide multi-layer fix (5 files / 4 dirs / 111 lines)
- Solved (7), by vulnerability family: auth / session / credentials x2, parsing / type confusion x2, injection (code / command / markup) x1, path / file handling x1, auth / session / credentials + path / file handling + information exposure x1
### Broke BOTH (replicate this shape): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines)


# Which techniques have broken the evaluated agents so far (measured)
## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 6 of 40 tagged tasks broke at least one model (15%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 20 | 2 | 2 | 1 | 15 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt, undici) |
| 2 | Already-protected-looking code | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 4 | One test per fix place | 40 | 2 | 3 | 1 | 34 | BASELINE (in 40/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 5 | Boundary-hugging functional tests | 38 | 2 | 3 | 1 | 32 | BASELINE (in 38/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 6 | Behavioural report, no localization, no scope | 39 | 2 | 3 | 1 | 33 | BASELINE (in 39/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 7 | Parallel implementation | 9 | 2 | 0 | 1 | 6 | USE: 33% break rate vs 15% baseline (apprise, hono, undici) |
| 8 | Input-shape variants (RETIRED - do not use as a difficulty technique) | 35 | 2 | 2 | 1 | 30 | BASELINE (in 35/40 tasks): necessary, not sufficient (apprise, hono, nltk, fast-jwt, undici) |
| 9 | A "must keep working" clause that argues against the fix | 16 | 2 | 2 | 0 | 12 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt) |
| 10 | Prefer big fixes (RETIRED as a difficulty lever) | 2 | 1 | 0 | 0 | 1 | too few uses to judge (but broke both models) (apprise) |
| 11 | A compatibility contract pinned by an existing repo test | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 12 | Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 13 | Producer off the check's path (M6, 5 of 17) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 14 | Wrong object (M10) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 15 | Merged / defaults route (M5) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._


# Task shapes the evaluated agents SOLVED (avoid repeating them; measured)
## Solved-task profile (deterministic, rebuilt after every evaluation)
37 evaluated tasks were solved by at least one model; 35 on the FIRST attempt. Median solve time 13 min. These are the shapes to avoid or to combine with the techniques that broke a model (see the technique scoreboard).
- Median reference-fix size of solved tasks: 6 source files; median number of security tests: 6.
- Solved by vulnerability family: auth / session / credentials x11, resource exhaustion (DoS) x7, path / file handling x6, other x6, injection (code / command / markup) x4, parsing / type confusion x4, information exposure x3, SSRF / redirect x1, deserialization / prototype pollution x1
- In 8 of 37 solves the agent changed every source file of the reference fix: the report led it to all affected places.

### Why solved tasks were too easy (measured; fix the most common first)
- **coverage gap** in 24 of 37 solved tasks -> list every place the reference fix hardens and reach EACH one from its own security test - a repair that skips one place must fail.
- **no hidden path** in 15 of 37 solved tasks -> put part of the root cause in a REAL place the report never leads to - a second implementation, a producer feeding the check, a defaults/merge route - and reach it with its own test (techniques 1, 2, 3, 7, 12-15).
- **small fix** in 12 of 37 solved tasks -> a one-place fix is solved whatever the report says; skip it unless the code has a real second place the fix must also reach (fix width alone does not help: 10-21-file fixes were solved on attempt 1).
- **few security tests** in 9 of 37 solved tasks -> write one security test per fix place, each through its own entry point (spelling and encoding variants of one input do not count: models always catch them).
- **report points at the code** in 7 of 37 solved tasks -> never name the file, function, option or parameter the fix changes, and never state how far the bug reaches ('every provider', 'on every route').

| Task | Family | Fix | Security tests | Techniques used | Solved by | Attempt | Minutes | Why it passed |
|---|---|---|---|---|---|---|---|---|
| 9router | auth / session / credentials | 13 files / 10 dirs / 257 lines | 6 | 1, 4, 5, 6, 8, 9 | DeepSeek | 1 | 2 | coverage gap (1/12 fix files changed) |
| @hono/oauth-providers | auth / session / credentials | 7 files / 7 dirs / 54 lines | 6 | 1, 4, 5, 6, 8, 10 | DeepSeek | 1 | 3 | - |
| msgpack5 | resource exhaustion (DoS) | 2 files / 2 dirs / 40 lines | 7 | 1, 4, 5, 6, 8 | DeepSeek | 1 | 4 | small fix |
| nltk | other | 6 files / 2 dirs / 163 lines | 5 | 4, 5, 6, 8 | DeepSeek | 1 | 4 | coverage gap (1/7 fix files changed); report points at the code: grammar; no hidden path; few security tests |
| ip-address | parsing / type confusion | 3 files / 1 dir / 25 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 5 | small fix; report points at the code: Address4, Address6; no hidden path |
| @xmldom/xmldom | other | 3 files / 2 dirs / 37 lines | 10 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 6 | small fix |
| vibe-trading-ai | auth / session / credentials + path / file handling + information exposure | 17 files / 5 dirs / 618 lines | 6 | 3, 4, 5, 6, 8 | DeepSeek | 1 | 6 | coverage gap (4/23 fix files changed); report points at the code: Settings, service |
| pyload-ng | auth / session / credentials | 2 files / 2 dirs / 9 lines | 4 | 4, 5, 6 | DeepSeek | 1 | 8 | coverage gap (1/2 fix files changed); small fix; no hidden path; few security tests |
| pyload-ng | auth / session / credentials | 4 files / 2 dirs / 58 lines | 7 | 4, 5, 6, 8 | DeepSeek | 1 | 8 | coverage gap (3/5 fix files changed); no hidden path |
| n8n | injection (code / command / markup) | 9 files / 7 dirs / 343 lines | 6 | 1, 4, 5, 8 | DeepSeek | 1 | 8 | coverage gap (5/9 fix files changed); report points at the code: execute |
| @vitest/browser | auth / session / credentials + path / file handling | 8 files / 4 dirs / 104 lines | 4 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 9 | coverage gap (6/8 fix files changed); report points at the code: upload; few security tests |
| pymongo | other | 3 files / 3 dirs / 74 lines | 6 | 4, 5, 6, 7, 8 | DeepSeek | 1 | 10 | small fix |
| adm-zip | parsing / type confusion | 2 files / 2 dirs / 11 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 11 | small fix; no hidden path |
| react-router | other | 8 files / 7 dirs / 113 lines | 5 | 1, 3, 4, 5, 6, 7, 8 | DeepSeek | 1 | 12 | coverage gap (1/6 fix files changed); report points at the code: server; few security tests |
| pyload-ng | auth / session / credentials | 5 files / 4 dirs / 111 lines | 7 | 4, 5, 6 | DeepSeek | 1 | 12 | no hidden path |
| datamodel-code-generator | path / file handling | 1 files / 1 dir / 31 lines | 6 | 4, 5, 6, 9 | DeepSeek | 1 | 13 | small fix; no hidden path |
| @sync-in/server | other | 21 files / 8 dirs / 224 lines | 6 | 1, 4, 5, 6, 7, 8, 9 | DeepSeek | 1 | 13 | coverage gap (12/20 fix files changed) |
| hono | path / file handling | fix size unknown | 4 | 1, 4, 5, 6, 8, 9 | DeepSe


# Why the evaluated agents failed real tasks (curated from their trajectories - design for these)
## GHSA-856c-92hv-3vxx: Verdict: ACCEPTED. Both models failed every run. DeepSeek scored 0.99 on all three attempts and MiMo scored 0.99 on all three. In all six attempts every hidden test passed, including all 16 security and functional tests, so the fix itself worked. Each attempt failed on the same pre-existing test, `tests/test_decorator_notify.py::test_notify_multi_instance_decoration`, which asserts `len(meta) == 8`. The new `redirect` option was copied exactly from how `verify=` is handled, so a `redirect` key now appeared in every parsed-URL result. The agents saw this test fail and changed the expected count to 9. Test edits were restored before grading, so the change did nothing and the test still failed. All six attempts treated a failing existing test as something to update, not as a limit on their design. None of them changed `apprise/asset.py`, which the reference fix did change. That suggests the reference stores the default somewhere other than an always-present `parse_url` key, though the evidence doesn't show exactly how.
#### Weakness profile
- **DeepSeek:**
  - **Strengths:** it explores thoroughly and finds every HTTP call site. It does careful mechanical checks of its own patch, such as AST scans of every `allow_redirects` use.
  - **Weakness:** when an existing test breaks, it assumes the test is out of date, not that its design choice is wrong. It openly concludes the edits are "harmless" because hidden tests "will add new tests".
  - **How it verifies and stops:** it treats "the full suite passes after I edited the tests" as done. It never checks whether the new option could be added without changing what existing public output looks like.
- **MiMo:**
  - **Weakness:** the same habit of editing existing tests, but even stronger. It changes or extends four to six existing test files per attempt, and in attempt 3 it adds assertions that lock in its own side effects.
  - **Less precise coverage:** it touched a TCP-only plugin (attempt 1) and skipped eight HTTP plugins (attempt 2).
  - **Why it stops:** its own tests pass, and it takes that as proof of correctness.
- **Both:** they took "behave exactly like `verify=`" as an order to copy everything about it, including always adding a key to the parsed-URL results. Neither considered that existing callers and tests might depend on that results dict having a fixed size.
#### Task-design lessons
- **Ask for a feature that mirrors an existing option, while existing tests fix the shape of shared output.** Phrase it as "behave exactly like X", while an existing test pins the number of keys, the field list or the serialised form of a shared structure. Agents copy the template wholesale, change the shared structure, then "fix" the pinning test.
- **Keep breakage-detecting tests in files the agent will naturally edit.** Enforce existing tests and restore any test edits before grading. Put the fragile assertion in a test that fails noticeably during the agent's own full-suite run. Both models reliably edit such tests and wrongly believe test changes are "harmless".
- **Make the reference fix put new state somewhere unexpected.** Here that was a central config or defaults object (`asset.py`) instead of the obvious parser. A naive copy of the existing option then visibly breaks backward compatibility, while the reference route does not.
- **Grade the security behaviour on every call site, not a sample.** Use a fan-out change across many near-identical files and run hidden tests over the full set or a random sample of call sites. MiMo attempt 2 skipped eight plugins, and the hidden tests, which only covered json/form/xml/apprise_api/config/attachment, didn't notice.
- **State backward compatibility outright, but leave the danger implicit.** Write "existing behaviour stays as it is today" and nothing more. Agents read that as runtime behaviour only. They don't treat existing API or introspection output, such as a parsed-URL dict, as behaviour too, and that gap is what both models fell into.

## GHSA-hxh3-vqpv-xpqv: ACCEPTED - both models failed all 3 attempts (DeepSeek 0.83/0.83/0.94, MiMo 0.89/0.94/0.89, Claude Code agent), every run stopped on its own (no timeout). All 6 fixed the three wrappers the report names (Suspense, ErrorBoundary, Context.Provider) and all 6 left `renderToString([unsafe, [unsafe]])` unescaped.
#### Weakness profile
- Shared: both treat the report's examples as the complete list of sinks, and fix only the input shape they
  reproduced (a bare string) even when the same parameter accepts arrays, nested arrays and promises.
- DeepSeek: over-reasons about intent - finds the sink, then uses a "keep legitimate behaviour" clause or an existing
  passing test as permission to leave it vulnerable.
- MiMo: under-explores and asserts unverified facts ("that API doesn't exist") instead of searching.
#### Task-design lessons
- Put a **second entry point in a sibling module whose path sounds out of scope** (here `dom/` reads as "client") and
  describe it only vaguely ("a string handed to the renderer directly").
- Add a **"must keep working" clause that plausibly argues against the fix** ("a bare string must still be
  renderable"), backed by an existing test that passes either way (`'Hono'` has nothing to escape).
- **Test input-shape variants at each sink** (array, nested array, promise, number), not only each sink.
- Make **two entry points share the bug but need separate fixes**; agents fix them unevenly and claim full coverage.
- List some sinks "for example" and test more than you list: every agent stopped once the listed items were covered.

## GHSA-6qxp-vccf-f47h: DeepSeek failed 3/3 (0.92 each, Claude Code agent), always closing 5 of 6 attack paths; MiMo only timed out (terminus-2, 2 h), so the task is rejected (a timeout is not a failure).
#### Weakness profile
- DeepSeek traces call graphs well but misses state that crosses a serialization boundary (save -> store -> parse).
- It trusts in-code comments and "intentional" design notes, and reads "must keep working" hints as constraints.
- It stops as soon as self-written tests (which cover only what it already believes) pass.
#### Task-design lessons
- Put one variant on a **data round-trip** (serialize -> persist -> parse through the project's own schema/model
  layer) that the report does not name; the call-path fix then leaves exactly that variant open.
- Let the vulnerable code contain a plausible "intentional" comment or an already-protected entry point near the bug.
- Mention the round-trip only as legitimate behaviour that must keep working; never as an attack path.

## GHSA-p4rw-rvv2-7xwr: DeepSeek failed all 3 attempts (0.93 each, always the toolbox symlink escape left open); MiMo failed 2 (0.87, toolbox + MTE left open) and solved 1. Rejected (MiMo solved). No timeouts; every run stopped on its own.
#### Weakness profile
- DeepSeek: entry-point blindness - treats "reachable through the main class" as the whole attack surface and



# Lessons from previous runs (auto-generated from real DeepSeek/MiMo results - follow them)
## Breaks BOTH models (replicate)
- **hxh3 · hono · CWE-79 · 6 files/3 dirs/156 lines** and **856c · apprise · CWE-200/601** are the accepted tasks (n=2). hono: both models scored 0.83–0.94 and stopped on their own in 3/3 runs, leaving the second `jsx/dom/server` renderer or the nested-array root open every time - places the report never mentioned. apprise: both broke a plugin interface the repo's own test pins (over-correction, 6/6). Check `stream > Should call onAbort` for flakiness before reusing hono.
- **Combine in one task:**
  1. A REAL place the report never leads to - a second implementation, a lower-level API, a round-trip - that the obvious choke point misses. This beat DeepSeek (n=3). Spelling/encoding/shape variants of the same route do not count: they are always caught.
  2. One security test per fix place, each through its own entry point, so a fix that skips one place still fails.
  3. A falsy or boundary variant (`0`, `""`, `[]`). This beat DeepSeek (tentative, n=1: x937).
  4. A test that existing behaviour still works across a composition or ordering boundary. This beat MiMo (tentative, n=1: vp8m).
  5. A path that is already safe, as a decoy. This beat MiMo (tentative, n=1: jq7h).
  6. Fast test suites. A MiMo timeout counts as "too slow", not as a failure (6qxp, vp8m).

## Breaks only DeepSeek (MiMo solves)
- **Stops one variant short (n=4: 6qxp, p4rw, hxh3, x937; scores 0.92–0.95).** It patches the first layer it finds, then declares itself done.
  - **p4rw · nltk · CWE-22/59.** It put the check in `CorpusReader.abspath` and missed the bare-string entry points `StandardFormat.open`, `XMLCorpusView` and `load_ace_file`. MiMo fixed the shared `FileSystemPathPointer`.
  - **x937 · fast-jwt · CWE-613 · 1 file/33 lines.** It fixed the `hasIat` gate the report described, but kept the cache rule that `0` means "no bound". The `exp: 0` case stayed open (13/14 tests passed). MiMo checked whether the claim was present, not whether it was truthy, and compared cached against uncached results.
  - **6qxp.** It saw that the binding is lost on a schema round-trip and stopped anyway.
- **Hiding file names is not enough.** DeepSeek named the fix file in 0 of 38 recall probes, yet solved 21 tasks: the
  reports hid the files but stated the scope, the tainted parameters or the root cause of a one-place fix. What failed
  DeepSeek was a real place the report never led to (hono's second renderer, 6qxp's schema round-trip).

## Breaks only MiMo (DeepSeek solves)
- **vp8m · undici · CWE-346 (tentative).** Security tests reached 1.0, but reuse in `compose(cache(), dns())` broke. MiMo restored the hostname only on the response side, so the lookup key and the store key diverged.
- **jq7h · pyload · CWE-613 (tentative).** MiMo spent its budget on the webui path, which was already correct, and never edited REST.
- **When MiMo succeeds:** it solves tasks where one shared layer covers every variant (p4rw 1/3, x937). It has 3 counted failures.
- **Evidence on MiMo is thin.** Its p90 step time is about 400 s vs about 40 s for DeepSeek. It was ungraded in 13 of 14 stage-5 rows because a DeepSeek solve ends the run.

## Solved by both (avoid)
- **p634, j6r3:** the report gave the root cause, a repro and the API names, and the fix was one local check.
- **pqg4, x33g:** both models named the fix location.
- **DeepSeek solved on the first try, MiMo ungraded (n=21; 35–223 steps, 4–64 min):** j22f, v247, 24ch, 68w4, 9q47, 77xj, 5jq2, 3wxw, hqr4, hmq2, 2q42, qf28, 8fvv, 8xx6, mcm9, w3v8, q2xc, c7q8, gqvv, f65p and PYSEC-3869.
  - Each had one choke point that every variant passed through.
  - Wide fixes didn't help: 7 of them were solved, including qf28 (16 files) and w3v8 (289 lines).

## Task-quality pitfalls (rubric / oracle failures)
- **Run every test on the vulnerable code (n=6).** Security tests must fail there and functional tests must pass.
  - 8r5x crashed before the injection ran.
  - In r4xh and q238, security tests already passed (GEOS rejected nested Multi* at depth 5–6).
  - mcm9 and vp8m had functional tests that required new behaviour.
  - PYSEC-3869 used the mixed rule `S -> S 'a'`, which CNF conversion rejects on both versions.
- **Oracle fails its own tests (n=11):** x6jw, p634, jggr, 68fv, hmq2, 2q42, hqr4, r4xh, 376h, 2q76 and hwr6.
  - If every functional test scores 0.0, the harness or fixture is broken. Regenerating fixed hmq2, 2q42 and hqr4.
  - Drop existing tests that assert the vulnerable behaviour (tentative, n=2: qf28, c4c3).
- **Tests accept only one fix shape (n=9):**
  - 68w4, 9q47, jq7h, qf28.
  - 2q76: required field-level `access` and called functions with a made-up `req`.
  - x78j: rejected raise, `SystemExit` and drop fixes.
  - p63j: aliased `@vitest/browser` to `utils.ts` and used fake contexts.
  - PYSEC-3819: mocked only the module-level `requests.get`.
  - 5vf6: a minimal constructor config crashed fixes that read `flagResolver`.

  Accept reject, raise, drop and sanitize fixes. Test through the public HTTP, CLI or RPC entry point. Mock at the transport layer and import through the package entry.
- **Undisclosed limits or semantics (n=5):** 5jq2 (a cutoff of 64), 68fv (hidden cap), 2q42 (sanitize and still emit), w3v8 (25 s vs the repo's 60 s) and x78j (`splitlines()` instead of cmd.exe rules). State limits in the report or use ≥100× margins, and model the real sink.
- **Weak tests (n=5):** x937, 6qxp, qf28, r4xh and 2q76 (deny-all passed). Assert the output content and make over-blocking fail. Count operations instead of timing them (tentative, n=2).
- **No network in tests (tentative, n=1: 5vf6).** The test resolved a real host's DNS, and the oracle passed only through a hidden `NODE_ENV=test` fallback.
- **Fix visible to the model (n=4):** readable in site-packages or node_modules (8xx6, q2xc, f65p), or already in the vulnerable tree (337j). Uninstall released copies.
- **Bad existing-test files (n=4):** helper, manual and DB-integration files. Exclude them.
- **Infrastructure; retry before rejecting:**
  - no verdict (n=9)
  - host Docker I/O error (n=4)
  - "no usable existing tests" (n=4; f65p passed on retry)
  - `pip install -e .` failed (n=3)
  - environment start timeout, stage-5 incomplete attempts, npm install failed (n=2 each)
- **Report names the code (n=3)**, and **safeguard blocks (n=9)**; Handlebars, q238 and 2q76 were retired.

## Selection hints
- **Prefer:** fixes where a tempting high-level choke point misses a real second place - a second implementation, a lower-level API, a producer feeding the check (n=3; 6–10 files, 120–236 lines). At screening, ask whether one function sees every variant. If it does, skip.
- **Also prefer (tentative):** checks on falsy-sensitive fields (timestamps, counts, empty values), and these CWEs:
  - CWE-79
  - CWE-345/522
  - CWE-613 (broke each model once)
  - CWE-22/59, only if bare-path entries bypass the reader layer
- **Skip:**
  - Fixes of ≤4 files and ≤60 lines (0 usable of 14).
  - DoS CWE-400/407/409/674/1284/1333 (0 usable).
  - CWE-22/73 fixed in one path builder (n=3).
  - CWE-91, URI parsers and SSRF fixes that need DNS (tentative).
  - Code generators.
  - Oracle patches over 80k characters (n=3).
  - Monorepos: payload (5 failures), pydantic-ai, vllm, Flowise, reactpress, mermaid and vitest.
  - PyPI repos where `pip install -e .` fails.
- **pyload:** use only with the real app's test client.
- **Recall:** reject if both models name the fix (n=2). Otherwise recall doesn't predict the outcome.


# Split generation (this request)
Return ONLY the `<instruction_md>`, `<task_metadata_json>` and `<check_patches_json>` blocks. Do NOT write the
<hidden_tests_py> block; it is requested in a separate step. Keep the check patches minimal (only the edits that
demonstrate shallow / removal / alternative behaviour).

