# Rancher: GitHub App team membership

Rancher is a Kubernetes management platform. When a user signs in through a GitHub App
that is installed in one or more GitHub organizations, Rancher derives the user's group
principals from the teams recorded in the app's installation data, stores them with the
user, and uses them to decide which clusters, projects and resources the user may reach.

The derivation is too broad. A user who belongs to one team in an organization is also
treated as a member of every other team in that organization. The user therefore gets the
access that was granted to teams they never joined: a cluster or project shared with one
team becomes reachable to every member of any team in the same organization.

The security property: at every point where access is decided, a user's effective team
membership must be exactly what the app's installation data currently records for that
user in each organization, no more and no fewer. Membership that the current data does not
record must never be effective for the user, and membership that it does record must never
be lost, however that membership is obtained, stored or reused.

Contracts:

- A request that is not authorized is refused, and a refused request changes nothing.
- Everything that works today keeps working exactly as today.
- The example above is an example, not the full set of affected places.

Constraints:

- Fix the reported problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or any existing implementation of it.
- Do not special-case the example.
- There is no network access.
