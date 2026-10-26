# A crafted media command can run a second program on the separate media host

AVideo is a video platform. Some installations run a separate media host that the main site drives
over HTTP: the host carries out media work described in payloads the main site sends, and runs it
as the web user.

We found that a client able to send such a payload can make the host run an unrelated operating
system command. The payload began with a normal FFmpeg invocation, so it looked like an ordinary
media job; the extra command still ran on the host.

## Security invariant

No client-supplied value may make the separate media host run any program other than the media
command the request describes, and no such value may start, extend or replace that command with
other shell work.

## Refusal

A request whose values cannot be run safely must not run the unsafe part. It may be refused with a
client error. A request that is refused must leave no side effect: no file, directory or process
created, changed or removed.

## What must keep working

Everything that works today keeps working exactly as it does today, and every legitimate input the
system accepts today is still accepted.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
