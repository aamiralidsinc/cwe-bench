# Credentials are replayed to a different origin on redirect

`urllib3` is a Python HTTP client library. Applications use it to call services and attach
request headers that belong to the origin they are talking to.

## Observed impact

Our service calls a partner endpoint with an `Authorization` header scoped to that endpoint.
The partner answers with a `302` whose `Location` points at a different host, and the client
sends the same `Authorization` header to that host. The second host logged a credential that
was never issued to it. The redirect itself was followed normally, so nothing looked wrong.

## Required behaviour

**A request header that carries the caller's credentials for one origin must never be sent to
a different origin.** Whenever following a redirect moves a request to another origin, the
client must withhold the headers that carried the caller's credentials for the original
origin, and must send everything else exactly as it does today. The redirected request must
still be made and the redirect target's response returned to the caller: withholding is not a
reason to fail, raise, or abandon the request.

This covers every credential the caller attached for the original origin, however it was
supplied and whichever header carries it.

Requests that stay on the same origin keep their headers.

Everything that works today keeps working exactly as today.

The example above is one way to reach the problem, not the full set.

## Contracts

- Withholding is silent. The redirected request is made without those headers and its response
  reaches the caller unchanged.
- Nothing else about a request or a response changes.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the
upstream fix. Do not special-case the example.
