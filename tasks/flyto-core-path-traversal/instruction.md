# Workflow modules write files outside the operator's sandbox directory

flyto-core is a workflow automation engine with several hundred modules. Clients run
them through the HTTP execution API, `POST /v1/execute`, or as steps of a workflow.
Many modules write files.
The operator confines all of that file output to one directory, the sandbox, set with
`FLYTO_SANDBOX_DIR` (the server's working directory when it is unset). Some modules
already refuse locations outside it; others do not.

## Observed impact

With `FLYTO_SANDBOX_DIR=/srv/flyto/sandbox`, a client sends:

```json
POST /v1/execute
{"module_id": "image.download",
 "params": {"url": "https://example.com/logo.png",
            "output_path": "/var/www/html/logo.png",
            "output_dir": "/var/www/html"}}
```

The response reports success and `/var/www/html/logo.png` now exists. Any API client
can write files anywhere the server process can.

This is one example, not the full set of affected modules or inputs.

## Required behaviour

- No caller-supplied parameter of any module run may cause a file or directory outside
  the sandbox to be created, overwritten, appended to or removed. This covers every file
  a module writes, for any purpose. It includes locations the module derives itself when
  the caller leaves the output location out.
- This holds however the location is spelled: absolute, relative, with `..` segments,
  or through a symbolic link inside the sandbox that points outside it.
- A run that would write outside the sandbox must be refused, not redirected to another
  location. A refused run fails cleanly. The response reports it as not ok (`"ok": false`), or
  with any 4xx status, and nothing outside the sandbox changes. That includes
  directories the run would otherwise have created.
- Locations inside the sandbox work exactly as today. That covers absolute paths,
  relative paths (resolved as today), spellings with `.` or `..` that still end up
  inside, sub-directories that do not exist yet (created as today), and default output
  locations that fall inside. For example, writing
  `/srv/flyto/sandbox/reports/2026/q3/chart.png` into a not-yet-existing
  `reports/2026/q3` must still succeed.
- Reading input files is out of scope for this report. Keep it as it is today.

## Constraints

- Fix the problem and its close variants, not only the example above.
- Keep all legitimate use working as it does today.
- Do not modify or add tests.
- Do not look up the upstream fix for this issue.
- Do not special-case the example's module, paths or values.
