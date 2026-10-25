# H4 shortlist (prior from screener records; confirm with the stacking reader, step 2)

771 records; 149 hosts already built; 80 offer both a DeepSeek-type and a MiMo-type trap; 51 of those are unbuilt.

| # | Entry | Repo | Score | Kinds | DS-type | MiMo-type | Routes | Language | Penalties | Family |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2350 | pypa/virtualenv | 33.0 | M1+M11+M3+M4+M5+M6 | True | True | 4 | Python (requires-pyt | - | download of code without integrity check (CWE-494), supply-chain/artif |
| 2 | 2714 | yt-dlp/yt-dlp | 33.0 | M1+M11+M2+M4+M5+M6 | True | True | 4 | Python (>=3.10 per p | - | unsafe file-type/name restriction (CWE-641): an allowlist of permitted |
| 3 | 12672 | budibase/budibase | 29.0 | M11+M3+M4+M5+M6 | True | True | 2 | TypeScript (yarn wor | - | CWE-200 exposure of sensitive information (stored datasource credentia |
| 4 | 5847 | python-social-auth/social-core | 29.0 | M11+M3+M4+M5+M6 | True | True | 2 | Python (>=3.10) | - | Session fixation (CWE-384): login CSRF via cross-session resume of a s |
| 5 | 9256 | hypequery/hypequery | 28.5 | M1+M11+M2+M4+M6 | True | True | 5 | TypeScript (ESM, Nod | - | SQL injection (CWE-89): missing neutralisation of string literals, raw |
| 6 | 480 | ultrajson/ultrajson | 28.0 | M1+M11+M2+M4+M6 | True | True | 4 | C extension for CPyt | - | CWE-20 improper input validation: UTF-8 sequence validation / silent U |
| 7 | 18880 | go-git/go-git | 27.5 | M1+M11+M2+M4+M6 | True | True | 3 | Go | - | CWE-22 path traversal (reference-name containment in the .git layout) |
| 8 | 26731 | spring-projects/spring-ldap | 27.5 | M1+M11+M2+M4+M6 | True | True | 3 | Java | - | CWE-287 improper authentication (LDAP simple bind accepts a DN with an |
| 9 | 12733 | bytebase/dbhub | 27.0 | M1+M11+M2+M4+M6 | True | True | 2 | TypeScript | - | CWE-184 / CWE-636 / CWE-863: an incomplete keyword blacklist used as a |
| 10 | 15921 | zalando/skipper | 27.0 | M1+M11+M2+M4+M6 | True | True | 2 | Go | - | incorrect authorization / fail-open on an incomplete request body (CWE |
| 11 | 12748 | nuxt-content/mdc | 26.0 | M1+M11+M4+M5+M6 | True | True | 3 | TypeScript (Nuxt mod | tiny_repo | xss: URL-scheme allow/deny bypass (CWE-184 incomplete denylist leading |
| 12 | 15705 | rancher/rancher | 26.0 | M11+M4+M5+M6 | True | True | 2 | Go | - | authorization / group membership (CWE-303 Incorrect Implementation of  |
| 13 | 7845 | microsoft/kiota-typescript | 26.0 | M11+M4+M5+M6 | True | True | 3 | TypeScript | - | credential exposure across origins on redirect through case-sensitive  |
| 14 | 33682 | guzzlehttp/psr7 | 25.5 | M1+M11+M4+M5+M6 | True | True | 3 | PHP | tiny_repo | URI host parsing differential / host confusion (CWE-20 improper input  |
| 15 | 18459 | dhax/go-base | 25.0 | M1+M11+M4+M5+M6 | True | True | 2 | Go | tiny_repo | CWE-798 use of hard-coded credentials / weak default secret in JWT sig |
| 16 | 7632 | ai/nanoid | 25.0 | M1+M11+M2+M4+M5+M6 | True | True | 4 | JavaScript (ESM, typ | tiny_repo;dos | Improper input validation leading to an unbounded loop (CWE-835, loop  |
| 17 | 723 | topoteretes/cognee | 24.5 | M1+M11+M4+M6 | True | True | 3 | Python >=3.10,<3.15 | - | missing authorization for a critical function (CWE-306 / CWE-862): wri |
| 18 | 19592 | maximhq/bifrost | 24.0 | M1+M11+M2+M4 | True | True | 6 | Go | - | CWE-918 server-side request forgery via an incomplete IP deny-list (CG |
| 19 | 2338 | apache/spark | 24.0 | M1+M11+M4+M6 | True | True | 4 | JavaScript (browser  | - | cross-site scripting (stored HTML injection in a web UI table; CWE-79, |
| 20 | 15304 | pocket-id/pocket-id | 23.5 | M11+M3+M4+M6 | True | True | 1 | Go backend + TypeScr | - | open redirect (CWE-601) |
