# H4 shortlist (prior from screener records; confirm with the stacking reader, step 2)

150 records; 55 hosts already built; 22 offer both a DeepSeek-type and a MiMo-type trap; 9 of those are unbuilt.

| # | Entry | Repo | Score | Kinds | DS-type | MiMo-type | Routes | Language | Penalties | Family |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 3745 | mlflow/mlflow | 25.5 | M1+M11+M4+M5 | True | True | 5 | Python | - | SSRF (CWE-918): user-controlled upstream URL in AI Gateway secret conf |
| 2 | 5900 | ibm/mcp-context-forge | 22.5 | M1+M11+M4+M6 | True | True | 3 | Python (plus unrelat | recall-high | server-side template injection (CWE-1336 / CWE-94), unsandboxed templa |
| 3 | 2366 | comfy-org/comfyui-manager | 22.0 | M1+M11+M2+M4 | True | True | 2 | Python (plus JS UI) | - | authorization bypass via unprotected alternate channel (trusted config |
| 4 | 4280 | senaite/senaite.core | 22.0 | M1+M11+M3+M4 | True | True | 3 | Python 2.7 (interfac | - | missing authorization (CWE-862) on state-changing JSON API routes; the |
| 5 | 794 | langflow-ai/langflow | 22.0 | M1+M11+M2+M4 | True | True | 2 | Python (backend) wit | - | authorization / IDOR (missing object-ownership and project scoping) co |
| 6 | 21576 | ericlbuehler/mistral.rs | 21.5 | M1+M11+M2+M4 | True | True | 2 | Rust | - | SSRF plus arbitrary local file read through an untrusted media source  |
| 7 | 11999 | nuxt/nuxt | 20.5 | M11+M4+M6 | True | True | 1 | TypeScript | - | authorization bypass via case-sensitivity mismatch between route-rule  |
| 8 | 5644 | netflix/lemur | 18.0 | M1+M11+M4 | True | True | 2 | Python | - | SSRF (CWE-918) via stored outbound URL; incomplete allowlist enforceme |
| 9 | 29156 | openremote/openremote | 17.5 | M11+M3+M4 | True | True | 1 | Java (+ Groovy Spock | - | Broken access control / IDOR (CWE-639): missing tenant (realm) scoping |
