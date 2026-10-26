# Remote names must stay inside the cluster configuration area

MicroCeph manages a Ceph cluster on a single host and can register other Ceph clusters as *remotes*, for example to replicate data between sites. An operator imports a remote with `microceph remote import <name> <token> --local-name <local>`, then lists or removes it with the other remote commands. Importing writes the remote's configuration and keyring files, named after the remote, into the local cluster's private configuration area, and later operations look the remote up by that name again.

## Observed problem

Importing a remote whose name contains path separators, such as `../../state`, writes the remote's configuration and keyring outside the configuration area. A crafted name therefore lets a client create, replace or delete files that the local cluster did not intend to touch.

## Required behaviour

Every name a client supplies for a remote, or for the local side of a remote, is untrusted, no matter where in a request it appears and no matter when it is used:

1. A usable name is 1 to 63 characters long, consists only of lowercase ASCII letters and digits, and is not the base name of a file or directory that the local cluster keeps in its own configuration area. Any other name must be rejected.
2. A request carrying an unacceptable name must fail rather than report success, and must leave the system unchanged: no file may be created, replaced or removed, and no record may be stored or dropped.
3. When a request identifies a remote in its path, it must act on exactly that remote. If the request body names a different remote, the request must fail with no effect.
4. The rules apply both to names supplied by the current request and to names stored by an earlier request and read back later.

These rules are one invariant, not a list of endpoints. Any way an untrusted name can reach a file path in the configuration area must obey them.

## What must keep working

- Names that satisfy the rules keep working exactly as today: they can be imported, listed, fetched and removed, and the features that consume a remote keep using it.
- A listing request that does not name a remote still lists all remotes.
- The local cluster keeps writing its own configuration and keyring files under the names it uses today, including names with dots.
- A name that merely resembles a reserved name (for example a reserved name with a digit appended) is still a legitimate remote name.

A refusal is a normal failure response; the request must not succeed and must not leave a partial effect behind.

The example above is one instance, not the complete set. Fix the problem and its close variants, keep legitimate use working, and do not special-case the example. Do not look up the upstream fix.
