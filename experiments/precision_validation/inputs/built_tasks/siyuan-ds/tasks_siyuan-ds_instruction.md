# Publish-mode access to workspace resources

SiYuan is a note-taking workspace. Its owner can publish selected material so
that visitors with reader access — visitors who are not the workspace owner —
can view it, without exposing the rest of the workspace. Besides that material,
the workspace stores other kinds of resource that can accompany it. Publication
is recorded in the workspace's own configuration.

**Observed impact.** A visitor with reader access could fetch stored material
the owner had withheld from publishing, and could learn about withheld material
from responses that describe it.

**Property.** Under any request, a visitor with reader access must never
obtain, and must never be told about, a stored resource that is not published
to that visitor. Publication has two paths, and a resource is published only
through one of them:

- the workspace's own selection or enablement settings for the resource make
  it available to readers, and any enabled or active state the workspace
  requires is satisfied; or
- the workspace establishes a resource's availability through its use by
  other content rather than through a selection of its own, and content
  available to the visitor uses it.

A resource that reaches neither path is not published and must never be
exposed, even when it carries a setting that merely fails to withhold it. A
response that describes a resource must follow the same rule as the resource
itself. A decision about a request must apply to the resource the
request actually resolves to, and a request must never resolve outside the area
assigned to it.

**Contracts.**

- A refusal is a client error, or a negative result code that carries none of
  the protected content; it is never a success and never a server error.
- A resource that is published to a visitor keeps being served exactly as it is
  today, at the same address and with the same content, and every request form
  that already yields published material keeps working.
- The workspace owner keeps unrestricted access to every resource and to
  complete descriptions.
- Apply this property uniformly to every response that returns or describes a
  stored resource.

**Constraints.**

- Fix the reported problem and its close variants.
- Keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix or the advisory.
- Do not special-case the examples.
