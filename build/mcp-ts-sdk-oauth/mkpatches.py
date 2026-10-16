"""Build the check patches: each is (base patch) + text edits, diffed against the vulnerable tree."""
import subprocess, sys, pathlib
W = pathlib.Path.home() / '.tb-graders/cwe/work/mcp-ts-sdk-oauth'
REPO = W / 'repo'
TASK = pathlib.Path('/Users/dev/terminal-bench/cwe-bench/tasks/mcp-ts-sdk-oauth')
OUT = pathlib.Path('/Users/dev/terminal-bench/cwe-bench/build/mcp-ts-sdk-oauth/checks')
UPSTREAM = pathlib.Path.home() / '.tb-graders/cwe/work/mcp-ts-sdk/hadi/mcp-ts-sdk-oauth-issuer-confusion_deepseek/task/solution/fix.patch'
REF = TASK / 'solution/fix.patch'
AUTH = 'packages/client/src/client/auth.ts'
CORE = 'packages/core/src/auth.ts'

def sh(*a):
    subprocess.run(a, cwd=REPO, check=True)

def edit(path, old, new, count=1):
    p = REPO / path
    s = p.read_text()
    assert s.count(old) == count, (path, old[:80], s.count(old))
    p.write_text(s.replace(old, new))

SINK_CHECK = """    // SEP-2352: the authorization server this request goes to. Client information stamped for a
    // different one is never presented here, whichever helper the request comes from.
    const issuer = metadata?.issuer ?? String(authorizationServerUrl);
    const boundIssuer = (clientInformation as StoredOAuthClientInformation | undefined)?.issuer;
    if (typeof boundIssuer === 'string' && !issuersMatch(boundIssuer, issuer)) {
        throw new AuthorizationServerMismatchError(boundIssuer, issuer);
    }
"""
SINK_NO_CHECK = """    const issuer = metadata?.issuer ?? String(authorizationServerUrl);
"""
STAMP = "        return { ...OAuthTokensSchema.parse(withoutIssuer(json)), issuer: metadata?.issuer ?? String(authorizationServerUrl) };"
NO_STAMP = "        return OAuthTokensSchema.parse(withoutIssuer(json));"
UNBOUND_A = """    // Tokens are issued to a client registration. Once the stored registration turned out to belong to
    // another authorization server, stored tokens that carry no stamp of their own (for example tokens an
    // application saved from the standalone token helpers) belong to that server too.
    const registrationBoundElsewhere = clientInformation === undefined && typeof rawClientInfo?.issuer === 'string';
"""
UNBOUND_B = """    if (tokens && tokens.issuer === undefined && registrationBoundElsewhere) {
        tokens = undefined;
    }
"""
MATCH = "    return a === b || (a.endsWith('/') && a.slice(0, -1) === b) || (b.endsWith('/') && b.slice(0, -1) === a);"

def v_upstream():
    pass

def v_miss_trap_helpers():
    edit(AUTH, SINK_CHECK, SINK_NO_CHECK)

def v_miss_trap_unbound_tokens():
    edit(AUTH, UNBOUND_A, "")
    edit(AUTH, UNBOUND_B, "")

def v_check_only():
    # the check without the data producer: the core schemas still strip the stamp
    edit(CORE, """        refresh_token: z.string().optional(),
        /**
         * Not part of the wire format: the authorization server this value was obtained from, added by
         * the client's `auth()` before it is stored and compared when it is read back (SEP-2352).
         */
        // eslint-disable-next-line unicorn/prefer-top-level-await -- Zod .catch(), not a Promise chain
        issuer: z.string().optional().catch(undefined)
""", """        refresh_token: z.string().optional()
""")
    edit(CORE, """        client_secret_expires_at: z.number().optional(),
        /**
         * Not part of the wire format: the authorization server this value was obtained from, added by
         * the client's `auth()` before it is stored and compared when it is read back (SEP-2352).
         */
        // eslint-disable-next-line unicorn/prefer-top-level-await -- Zod .catch(), not a Promise chain
        issuer: z.string().optional().catch(undefined)
""", """        client_secret_expires_at: z.number().optional()
""")

def v_origin_only_compare():
    edit(AUTH, MATCH, "    return new URL(a).origin === new URL(b).origin;")

def v_prefix_compare():
    edit(AUTH, MATCH, "    const x = a.replace(/\\/$/, ''), y = b.replace(/\\/$/, '');\n    return x.startsWith(y) || y.startsWith(x);")

def v_secret_only():
    # only client information carrying a client_secret is checked; signing keys/assertions are not
    edit(AUTH, "    if (typeof boundIssuer === 'string' && !issuersMatch(boundIssuer, issuer)) {",
         "    if (typeof boundIssuer === 'string' && (clientInformation as { client_secret?: string } | undefined)?.client_secret && !issuersMatch(boundIssuer, issuer)) {")
    edit(AUTH, "        if (rawClientInfo && checked === undefined) {",
         "        if (rawClientInfo && checked === undefined && (rawClientInfo as { client_secret?: string }).client_secret) {")
    edit(AUTH, "        return checked;\n    };", "        return checked ?? (rawClientInfo?.client_secret ? undefined : rawClientInfo);\n    };")

def v_check_before_prepare_only():
    # the check runs once, before the provider prepares the request; a later read is unchecked
    edit(AUTH, SINK_CHECK, SINK_NO_CHECK)
    edit(AUTH, "    clientInformation ??= await readClientInformation();",
         "    clientInformation ??= await provider.clientInformation({ issuer });")

def v_refuse_unbound():
    # fail closed on any credential without a stamp
    edit(AUTH, "        return stored.issuer === undefined ? stored : { ...stored, issuer: undefined };\n    }",
         "        return undefined;\n    }")
    edit(AUTH, "        if (rawClientInfo && checked === undefined) {\n            throw new AuthorizationServerMismatchError(String(rawClientInfo.issuer), issuer);",
         "        if (rawClientInfo && checked === undefined) {\n            throw new AuthorizationServerMismatchError(String(rawClientInfo.issuer ?? 'unknown'), issuer);")

def v_throw_on_mismatch_in_auth():
    # auth() refuses outright whenever stored client information names another server
    edit(AUTH, "    if (clientInformation === undefined && rawClientInfo?.issuer && provider.saveClientInformation === undefined) {",
         "    if (clientInformation === undefined && rawClientInfo?.issuer) {")

def v_disable_feature():
    edit(AUTH, "    let clientInformation = await readClientInformation();",
         "    let clientInformation = await readClientInformation();\n    if (clientInformation) throw new AuthorizationServerMismatchError(String(clientInformation.issuer), issuer);")

def v_alt_correct_fix():
    # Trap fixes written differently: per-helper checks in the refresh/code-exchange helpers instead
    # of the shared sink, and the helpers stamping the tokens they return with the issuing server
    # instead of auth() ignoring unbound tokens (changes the helpers' return value).
    edit(AUTH, SINK_CHECK, "")
    edit(AUTH, UNBOUND_A, "")
    edit(AUTH, UNBOUND_B, "")
    edit(AUTH, NO_STAMP, STAMP)
    edit(AUTH, """function issuersMatch(a: string, b: string): boolean {""", """function assertBoundTo(clientInformation: OAuthClientInformationMixed, authorizationServer: string): void {
    const stamp = (clientInformation as StoredOAuthClientInformation).issuer;
    if (typeof stamp === 'string' && !issuersMatch(stamp, authorizationServer)) {
        throw new AuthorizationServerMismatchError(stamp, authorizationServer);
    }
}

function issuersMatch(a: string, b: string): boolean {""")
    edit(AUTH, """    const tokenRequestParams = prepareAuthorizationCodeRequest(authorizationCode, codeVerifier, redirectUri);
""", """    assertBoundTo(clientInformation, metadata?.issuer ?? String(authorizationServerUrl));
    const tokenRequestParams = prepareAuthorizationCodeRequest(authorizationCode, codeVerifier, redirectUri);
""")
    edit(AUTH, """    const tokenRequestParams = new URLSearchParams({
        grant_type: 'refresh_token',
        refresh_token: refreshToken
    });
""", """    assertBoundTo(clientInformation, metadata?.issuer ?? String(authorizationServerUrl));
    const tokenRequestParams = new URLSearchParams({
        grant_type: 'refresh_token',
        refresh_token: refreshToken
    });
""")

def v_hardening_fix():
    # reference + defensive hardening of the code the tests import
    edit(AUTH, SINK_CHECK, SINK_CHECK + """    // Metadata must describe the authorization server the request is addressed to.
    if (metadata && !issuersMatch(metadata.issuer, String(authorizationServerUrl))) {
        throw new AuthorizationServerMismatchError(metadata.issuer, String(authorizationServerUrl));
    }
""")
    edit(AUTH, "    return OAuthClientInformationFullSchema.parse(withoutIssuer(await response.json()));",
         "    return { ...OAuthClientInformationFullSchema.parse(withoutIssuer(await response.json())), issuer: metadata?.issuer ?? String(authorizationServerUrl) };")
    edit(CORE, "        issuer: z.string().optional().catch(undefined)\n    })\n    .strip();\n\n/**\n * RFC 8693",
         "        issuer: z.string().url().optional().catch(undefined)\n    })\n    .strip();\n\n/**\n * RFC 8693")
    edit(CORE, "        issuer: z.string().optional().catch(undefined)\n    })\n    .strip();\n\n/**\n * RFC 7591 OAuth 2.0 Dynamic Client Registration full",
         "        issuer: z.string().url().optional().catch(undefined)\n    })\n    .strip();\n\n/**\n * RFC 7591 OAuth 2.0 Dynamic Client Registration full")

VARIANTS = {
    'upstream_fix': (UPSTREAM, v_upstream),
    'miss_trap_helpers': (REF, v_miss_trap_helpers),
    'miss_trap_unbound_tokens': (REF, v_miss_trap_unbound_tokens),
    'check_only': (REF, v_check_only),
    'origin_only_compare': (REF, v_origin_only_compare),
    'prefix_compare': (REF, v_prefix_compare),
    'secret_only': (REF, v_secret_only),
    'check_before_prepare_only': (REF, v_check_before_prepare_only),
    'refuse_unbound': (REF, v_refuse_unbound),
    'throw_on_mismatch_in_auth': (REF, v_throw_on_mismatch_in_auth),
    'disable_feature': (REF, v_disable_feature),
    'alt_correct_fix': (REF, v_alt_correct_fix),
    'hardening_fix': (REF, v_hardening_fix),
}

only = sys.argv[1:] or list(VARIANTS)
for name in only:
    base, fn = VARIANTS[name]
    sh('git', 'checkout', '-q', '--', '.')
    sh('git', 'apply', str(base))
    fn()
    diff = subprocess.run(['git', 'diff'], cwd=REPO, check=True, capture_output=True, text=True).stdout
    (OUT / f'{name}.patch').write_text(diff)
    print(name, len(diff.splitlines()))
sh('git', 'checkout', '-q', '--', '.')
