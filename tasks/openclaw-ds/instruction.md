# Feishu tool permissions are not enforced when a tool runs

OpenClaw's Feishu (Lark) channel plugin gives the assistant a set of workplace tools over the
company's Feishu workspace. One OpenClaw instance can hold several Feishu accounts (different apps
or tenants), and the operator decides **per account** which of those tools the assistant may use. A
tool is offered to the assistant whenever at least one configured account allows it.

Reported: the per-account decision is not applied when a tool actually runs.

Example: an operator runs two Feishu accounts. Documents are disabled for the account the assistant
session is bound to and enabled for the other one. The assistant is still able to read a document:
the request succeeds and the document's blocks come back from the account that is not allowed to
serve document requests.

## What must hold

No assistant operation may run through a Feishu account whose effective configuration disables the
tool being used — whether the account was named in the request, taken from the session, or chosen
by the product when the request names none, and even though the tool is offered because a different
account allows it.

When a request names no account, it must still be served by an account that is allowed to serve it
whenever one exists.

An account's effective configuration is what the product derives for that account, including the
defaults it applies to settings that account never mentions.

A refused request returns an error result and performs no Feishu operation through the refused
account: nothing is read, written or sent.

Everything an operator allows keeps working exactly as it does today, for every account and every
tool.

The example above is an example, not the full set.

## Constraints

- Fix the reported problem and its close variants; do not special-case the example.
- Keep legitimate use working.
- Do not consult or reproduce the upstream fix; work from this report and the code you have.
