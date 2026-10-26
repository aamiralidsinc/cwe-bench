# In-app notification destinations can navigate a subscriber's session to a sender-chosen address

## The system
This repository is a notification platform. A workflow run produces in-app notifications for a
subscriber; each notification can carry a destination (a web address plus a window target) on the
notification itself and on its primary and secondary action buttons. Those destinations may be
written into the workflow as literals or assembled from data supplied when the workflow is
triggered, so the value that ends up on a delivered notification can be chosen by whoever triggers
the workflow. Subscribers read their notifications through applications built on the product: the
product hands notifications to those applications, and the built-in notification view follows a
destination when the subscriber opens a notification or one of its actions.

## Observed impact
A workflow trigger supplies an action destination in the form of a script address. The subscriber
receives the notification, and when the subscriber opens it the notification view follows that
address inside the subscriber's session instead of a web page, so the sender's content runs with
the privileges of the subscriber's session. A harmless way to observe it: the notification that
arrives carries the sender-chosen address unchanged even though it is not a web address.

## What must hold
For every in-app notification the product makes available to a subscriber's application, and for
every part of one that carries a destination (the notification itself, its primary action and its
secondary action), the destination must be safe to follow:

- an absolute http or https address, or
- a relative path that begins with exactly one slash,

either of which may contain template variables; and its window target must be one of the
browsing-context names the product already accepts for notification actions.

No other scheme and no document-embedding address may be presented or followed, and only an
absolute http or https address may name a host: a relative path must never be reinterpreted as an
address on another host. This holds no matter how the destination was produced, stored or relayed,
and on every surface through which the product hands a notification, or notification data, to a
subscriber's application or renders it for a subscriber.

## Contracts
- **Omission, not substitution.** A destination that cannot be presented safely is omitted: the
  notification is still presented, without that destination. It is never replaced with another
  destination or a placeholder.
- **Unsupported window target.** A legitimate destination paired with an unrecognised window
  target must keep the destination; only the target is omitted or replaced with a supported
  default.
- **Preservation.** Everything that works today keeps working exactly as it does today:
  - absolute http and https destinations, with any supported window target;
  - single-slash relative paths, including the ones the host application routes itself;
  - destinations that begin with a template variable, and template variables inside absolute or
    relative destinations.
- A part of the product may not assume that another part has already filtered a destination before
  it presents it.
- The forms above are examples, not an exhaustive list; reason about the property, not the
  samples.

## Constraints
- Fix the problem and its close variants, not just the sample.
- Keep every legitimate use working.
- Do not look up the published upstream fix for this issue.
- Do not special-case the example inputs.
