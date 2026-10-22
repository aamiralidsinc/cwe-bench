# Credentials reach other hosts when requests are redirected

electron-builder packages and publishes Electron apps. Its auto-update library lets a packaged app check for, download and install new versions from GitHub, GitLab, S3 or any HTTP server. Both make HTTP requests that often carry credentials: publish tokens, private-repository tokens, and headers an application sets for its own update server.

## What we observed

An app checks for updates against a self-hosted GitLab instance, configured with a GitLab project access token. When the updater requests the release's update-info file, GitLab answers with a redirect to an object-storage host on another domain, which is a normal setup for uploads. The object-storage host's access logs contain the project access token.

## Required behaviour

- No credential attached to a request may reach an origin (scheme, host and port) other than the one it was attached for. Credentials include any request header that authenticates the client or user, standard or application-specific. This holds for every request the updater and the build and publish tooling make, at every redirect.
- No secret the tooling is given may appear in clear text in an error message or in debug output (`DEBUG=electron-builder`). Secrets include any credential value, whatever the field, option or variable holding it is called.

## Must keep working

- Redirects keep working. After a redirect to another origin, the request still completes there without the credentials. Ordinary headers such as `Accept` or `User-Agent` still go along.
- Redirects within the same origin keep the credentials. So does an `http` to `https` upgrade on the same host with default ports. Private servers must keep working.
- Everything else works exactly as it does today: update checks, update downloads and publishing, including configuration validation and its error messages. Debug output still shows data that is not secret.

The service and setup above are examples, not the full set.

## Constraints

- Fix the problem and its close variants, not only the example above.
- Keep legitimate use working as described.
- Do not modify or add tests.
- Do not look up the upstream fix.
- Do not special-case the example.
