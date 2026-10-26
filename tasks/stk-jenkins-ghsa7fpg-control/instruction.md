# Job configuration lets an editor launch jobs they may not build

Jenkins is a build automation server. A user who may edit a job's configuration can add a
post-build step that starts other jobs. The server never asks whether that user is allowed to
build the jobs it will start.

Impact: a user who is allowed to configure only their own job can make it start a restricted
production job, which then runs with the server's authority, without ever being allowed to
build it. One observed case: a user holding read and configure on a single free-style job, and
only read on a restricted job, saves the configuration with the restricted job named in the
build-other-projects step; the save is accepted, and the restricted job starts when the first
job builds.

The property: a configuration write must not leave the written job configured to start another
job that the user making the write is not allowed to build. Where it would, the write must be
refused.

Contracts:
- A refusal is a client error and has no effect.
- Everything that works today keeps working.
- Fix the problem and its close variants. Do not look up an upstream fix. Do not special-case
  the example.
