# proot-distro: unpacked content must stay inside the container

proot-distro creates and manages Linux containers that run under proot. It can install a
container from a root filesystem tarball or a local Docker/OCI image archive, restore a container
from a backup archive, and build a container image from a Dockerfile whose COPY and ADD steps
write files into a staging root filesystem.

## Observed impact

A root filesystem archive that carries a symbolic link pointing outside the container, followed
by an entry underneath that name, is unpacked onto the host. For example

    proot-distro install ./rootfs.tar -n demo

where `rootfs.tar` contains a link named `shared` whose target is `/srv/state` and then a regular
file `shared/hosts`, leaves `/srv/state/hosts` created or overwritten on the host machine while
the command reports success.

## Required property

Content supplied by an archive, image or backup — every member of it, whatever its type, name,
target or position — must never cause proot-distro to create, change, delete or read any file or
directory outside the container it is working on. This holds wherever in the operation the path
is used, including for material that was unpacked earlier and acted on later.

Paths used for container content mean what they mean inside that container. An absolute symbolic
link target names a location in the container's own filesystem (the container's `/`), `..` never
climbs above the container's root, and a relative target is resolved from the link's own
location. Following a link therefore lands inside the container, at the place the link names
there, never on the host.

## Contracts

- An entry that cannot be placed inside the container may be refused, and a refusal may be
  reported as an error; either way, nothing outside the container may be created, changed or
  deleted, and nothing outside it may be read into the container.
- Everything that works today keeps working exactly as today. In particular, symbolic links are
  stored with their original targets; a relative link inside a container is followed to the place
  it names in that container; an absolute link target refers to the container root and is followed
  there; ordinary files, directories and hard links land at their usual in-container paths; a
  container's normal configuration is still written inside the container; and a well-formed
  image, backup or Dockerfile still builds, installs or restores completely.
- The behaviour applies to every operation on container content, not only to the example above.
  The example is one example — it is not the complete set of entry points, member types or path
  shapes.

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix, and do not special-case the example.
