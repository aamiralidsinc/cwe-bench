# Saved theme colours can make the forum read server files

Flarum is forum software. Administrators configure the forum's appearance from the admin panel,
including the theme colours that are compiled into the stylesheet every visitor downloads.

## Impact

An administrator who saves a theme colour can put more than a colour into the value. When Flarum
builds the stylesheet from the saved settings, the extra content makes the compiler read a file
from the server's filesystem, and the file's contents are published in the public stylesheet. The
save itself looks like an ordinary successful settings update, so nothing warns the operator.

For example, saving a theme colour from the admin panel's appearance page is enough to make the
generated stylesheet contain the contents of a file that the administrator names.

## The property

No value that an administrator submits may make the style build read a local file or contact a
network endpoint. This is a property of the value itself: however the value reaches the generated
stylesheet, it must not be able to do either.

## Contracts

- When the product rejects such a submission, the rejection is a client error and leaves no
  setting or generated file behind. A server error is not a rejection.
- Every legitimate value keeps working exactly as it does today, and valid stylesheets continue
  to compile.
- Fix the problem and its close variants.
- Do not look up the upstream fix or any existing implementation of it.
- Do not special-case the example.
- There is no network access.
