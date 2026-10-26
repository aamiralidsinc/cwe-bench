# Administrator credentials must not be fixed

## The system

Homer is a SIP capture platform. Its coordinator process serves the web and API tier and can
authenticate operators locally: an administrator account lives in the coordinator's settings
database, and people sign in with a username and password. A deployment describes its coordinator
with a configuration file, or with environment overrides of the same settings.

The setting that selects this built-in sign-in is the coordinator's authentication setting. It may
be the single word for the local provider, an object of the same shape with a `type`, or absent
entirely, all of which mean the same thing. It may also carry the administrator's username and a
stored password credential (`admin_password_hash`).

## Observed problem

Start the coordinator from a minimal configuration that selects built-in sign-in and never mentions
an administrator password. The account `admin` is then reachable with the password `sipcapture` —
the first-login password the project has always documented. Anyone who has read the product's
public documentation can sign in to every such deployment as an administrator. The operator never
chose that password, and it is not a secret.

## Security property

At no time may an administrator account be reachable with a credential whose value is the same on
every installation. Whenever the operator has not supplied a credential, the credential that ends
up in effect must be freshly generated and unpredictable, and it must be disclosed once so the
operator can sign in. This holds regardless of how the credential came to be in effect.

Refusing safely is acceptable: an operation that cannot establish a fresh credential must return a
client-visible error and leave no credential behind.

## Keep working

- A credential the operator supplies explicitly stays in effect exactly as supplied, in either
  stored form the product accepts today; it is still the credential in effect the next time the
  deployment starts.
- An administrator row that already exists is not changed at startup, and every credential stored
  by an installation today keeps authenticating.
- A deployment with no operator-supplied credential still starts and is usable: it issues a fresh
  credential, disclosed once, instead of failing closed.
- A blank or whitespace-only value means "not supplied".
- Sign-in with the operator's username and password keeps behaving as today, including refusing a
  wrong password.

`admin` / `sipcapture` is the case that was reported; the same property applies to every way an
administrator credential can be put in place. These are examples, not the full set.

## Constraints

- Fix the underlying problem and its close variants, not just the example.
- Keep every legitimate use working.
- Do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
