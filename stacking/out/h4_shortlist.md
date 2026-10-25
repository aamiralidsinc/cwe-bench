# H4 shortlist (prior from screener records; confirm with the stacking reader, step 2)

250 records; 55 hosts already built; 34 offer both a DeepSeek-type and a MiMo-type trap; 21 of those are unbuilt.

| # | Entry | Repo | Score | Kinds | DS-type | MiMo-type | Routes | Language | Penalties | Family |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 25731 | jenkinsci/jenkins | 30.0 | M1+M11+M4+M5+M6 | True | True | 4 | Java | - | CWE-502 unsafe deserialization / type confusion in XStream unmarshalli |
| 2 | 16 | onionshare/onionshare | 26.5 | M1+M11+M3+M4+M6 | True | True | 3 | Python | - | CWE-59 link following / path containment (file disclosure from shared  |
| 3 | 15092 | filebrowser/filebrowser | 26.0 | M1+M11+M3+M4+M6 | True | True | 4 | Go | regression_tests_in_pinned_commit | CWE-59 symlink following / CWE-22 path traversal out of a per-user fil |
| 4 | 3745 | mlflow/mlflow | 25.5 | M1+M11+M4+M5 | True | True | 5 | Python | - | SSRF (CWE-918): user-controlled upstream URL in AI Gateway secret conf |
| 5 | 23237 | apolloconfig/apollo | 25.5 | M11+M4+M5+M6 | True | True | 1 | Java | - | authentication bypass via identity parsing / canonicalisation differen |
| 6 | 17933 | goshs-labs/goshs | 25.0 | M1+M11+M4+M5 | True | True | 4 | Go | - | Improper access control / incomplete mode-flag enforcement: a destruct |
| 7 | 480 | ultrajson/ultrajson | 23.5 | M1+M11+M4+M6 | True | True | 3 | C (CPython extension | - | CWE-20 improper input validation: incomplete UTF-8 well-formedness che |
| 8 | 7491 | jovancoding/network-ai | 23.5 | M1+M11+M4+M6 | True | True | 2 | TypeScript | - | CWE-22/CWE-73 path traversal via externally controlled persisted file  |
| 9 | 6261 | xorbitsai/inference | 23.0 | M1+M11+M4+M6 | True | True | 2 | Python | recall-high | code injection (CWE-95 eval of untrusted/model-generated text) |
| 10 | 5900 | ibm/mcp-context-forge | 22.5 | M1+M11+M4+M6 | True | True | 3 | Python (plus unrelat | recall-high | server-side template injection (CWE-1336 / CWE-94), unsandboxed templa |
| 11 | 2366 | comfy-org/comfyui-manager | 22.0 | M1+M11+M2+M4 | True | True | 2 | Python (plus JS UI) | - | authorization bypass via unprotected alternate channel (trusted config |
| 12 | 4280 | senaite/senaite.core | 22.0 | M1+M11+M3+M4 | True | True | 3 | Python 2.7 (interfac | - | missing authorization (CWE-862) on state-changing JSON API routes; the |
| 13 | 794 | langflow-ai/langflow | 22.0 | M1+M11+M2+M4 | True | True | 2 | Python (backend) wit | - | authorization / IDOR (missing object-ownership and project scoping) co |
| 14 | 21576 | ericlbuehler/mistral.rs | 21.5 | M1+M11+M2+M4 | True | True | 2 | Rust | - | SSRF plus arbitrary local file read through an untrusted media source  |
| 15 | 19198 | enchant97/note-mark | 21.0 | M1+M11+M4+M6 | True | True | 2 | Go | tiny_repo | path traversal (CWE-22) via stored identifiers used as path components |
| 16 | 11999 | nuxt/nuxt | 20.5 | M11+M4+M6 | True | True | 1 | TypeScript | - | authorization bypass via case-sensitivity mismatch between route-rule  |
| 17 | 25622 | omnifaces/omnifaces | 19.5 | M1+M11+M3+M4+M5 | True | True | 3 | Java | tiny_repo;many_fix_commits;dos | CWE-345/CWE-862 trust of client-forged resource identifier (allow-list |
| 18 | 5644 | netflix/lemur | 18.0 | M1+M11+M4 | True | True | 2 | Python | - | SSRF (CWE-918) via stored outbound URL; incomplete allowlist enforceme |
| 19 | 29156 | openremote/openremote | 17.5 | M11+M3+M4 | True | True | 1 | Java (+ Groovy Spock | - | Broken access control / IDOR (CWE-639): missing tenant (realm) scoping |
| 20 | 12398 | medplum/medplum | 17.5 | M11+M3+M4 | True | True | 1 | TypeScript | - | open redirect / redirect URI validation (OAuth authorization code leak |
