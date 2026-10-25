# Workflow modules write files outside the operator's sandbox directory

flyto-core is a workflow automation engine with several hundred modules. Clients run
modules one at a time through the HTTP execution API, `POST /v1/execute`, with a
`module_id` and a `params` object, or as steps of a workflow. Many modules write files.

The operator confines all file output to one directory, the sandbox, set with
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

The response reports success (`"ok": true`) and `/var/www/html/logo.png` now exists.
Any API client can write files anywhere the server process can.

This is one example, not the full set of affected modules or inputs.

## Required behaviour

- No caller-supplied value may cause a file or directory outside the sandbox to be
  created, overwritten, appended to or removed. This covers every file a run writes or
  removes, for any purpose: the module's main output, extra files it keeps beside it,
  and locations it derives itself when the caller leaves a location out.
- The rule applies to every value that becomes part of a location, not only values
  spelled as paths. A name, label or file name that a module joins into a location is
  covered the same way.
- This holds however the location is spelled: absolute, relative, with `..` or `.`
  segments, or through a symbolic link inside the sandbox that points outside it.
- A run that would touch such a location must be refused, not redirected to another
  location. A refused run fails cleanly: the execution API reports it as not ok
  (`"ok": false`), or the request returns any 4xx status, and nothing outside the
  sandbox changes. That includes directories the run would otherwise have created and
  files it would otherwise have removed.
- Locations inside the sandbox work exactly as today. That covers absolute paths,
  relative paths (resolved as today), spellings with `.` or `..` that still end up
  inside, sub-directories that do not exist yet, default output locations that fall
  inside, and names containing dots or spaces. For example, writing
  `/srv/flyto/sandbox/reports/2026/q3/chart.png` into a not-yet-existing
  `reports/2026/q3` must still succeed, as must a report whose name contains a version
  such as `release.2026`.
- Reading input files is out of scope for this report. Keep it as it is today.

## Constraints

- Fix the problem and its close variants, not only the example above.
- Keep all legitimate use working as it does today.
- Do not modify or add tests.
- Do not look up the upstream fix for this issue.
- Do not special-case the example's module, paths or values.
