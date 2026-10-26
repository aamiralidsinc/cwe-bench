# DevGuard: visitors can change data on publicly readable resources

DevGuard is a vulnerability-management platform. Organizations contain projects, projects contain assets, and each asset has named versions ("refs") that carry what the product knows about it: dependency and first-party vulnerabilities, licence risks, VEX rules, artifacts and external references. Teams work on those records — they triage findings, record assessment events and mitigation decisions, decide licence risks, and maintain VEX rules.

An organization, a project or an asset can be made publicly readable, so that people outside the team can see its security posture without being given a seat in the organization.

## What was observed

A signed-in user who has no membership in a public organization can send an assessment event for one of its dependency vulnerabilities and receives an ordinary success response; the event is written exactly as if the caller belonged to the team. The same is possible for the other kinds of record the product keeps for a publicly readable resource.

## What must be true

Access that comes from a resource being publicly readable — rather than from membership in that same resource — may never be used to change data belonging to it. A request that got this far only because of public visibility must be refused, whatever operation carries the change, and no matter which level of the hierarchy granted the visibility.

A refused request responds with a client error (4xx) and leaves nothing changed. An allowed request behaves exactly as it does today.

## What must keep working

Nothing that works for members may regress. A member whose access to a resource is read-only must keep being able to record assessment decisions on the findings they can see: triaging a vulnerability, mitigating it, deciding a licence risk, or creating, changing and removing a VEX rule. Public read access must keep working for everyone, signed-in visitors included.

The example above is one example, not the full set of entry points or request forms the rule covers. Fix the problem and its close variants without special-casing the endpoints named here; keep legitimate use working; and do not look up the upstream project's own fix.
