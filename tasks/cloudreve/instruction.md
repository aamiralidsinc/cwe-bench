# Security review: self-hosted cloud file server

The repository in `/app` is a self-hosted cloud file-management and sharing
server written in Go. It exposes an HTTP API under `/api/v4` and serves a file
browser, an online document editor, file sharing, and a live activity feed.
During a review we reproduced the following problems against a running instance
(local storage backend, built-in database — no external services). Each is
triggered through the server's real HTTP interface by an ordinary authenticated
user. Please correct the underlying behaviour.

## Observed problems

**Deactivated accounts leak through account search.** An authenticated user
who calls the account-search endpoint with a keyword receives back accounts
whose status is *not* active — deactivated or banned accounts show up alongside
active ones, disclosing their existence, email address and display name. Search
must only ever return accounts that are currently active.

**A thumbnail request can be turned into a memory-exhaustion attack.** If a user
uploads an image file whose header *declares* an enormous pixel size (a tiny,
highly compressible file that claims, say, tens of millions of pixels) and then
asks the server for that file's thumbnail, the server tries to decode the whole
image, allocating memory proportional to the declared width times height. A
single small upload can therefore drive the process to exhaust memory. Images
whose declared dimensions are implausibly large must be refused for thumbnailing
before any full decode is attempted, while normal images (for example an
ordinary 24-megapixel camera photo) must still thumbnail.

**The online editor's "save as" can write outside the source directory.** The
online/collaborative editor supports creating a new file relative to the one
being edited, taking a caller-supplied suggested target name. When that name
contains path separators and parent-directory segments, the server resolves it
and writes the new file *outside* the directory of the file being edited. The
suggested target must be treated as a bare file name that cannot escape the
source file's own directory. A plain file name must still work.

**The online editor's access token is accepted without its secret.** A session
for the editor hands the client an access token made of a session identifier
and a secret, separated by a dot. Requests to the editor endpoints that present
a correct session identifier but a wrong (or junk) secret are nevertheless
accepted and operate on the file. Possessing the session identifier alone should
not be enough: the complete token, secret included, must be validated, while a
correctly issued token must keep working.

**A single-file share lets its holder subscribe to folder-wide activity.** A
single-file share is meant to expose exactly one file. However, the holder of
such a share can open the server's live activity (event) stream through the
share and begin receiving events — and that stream is scoped to the containing
folder, so it leaks activity about other files in the owner's folder that were
never shared. Subscribing to the activity stream through a single-file-share
view must be refused, while a user subscribing to a folder they own must keep
working.

## What must hold

After your change, every one of the behaviours above must be closed when
exercised through the HTTP API, and the legitimate counterparts (logging in,
uploading and listing files, searching for active users, thumbnailing normal
images, using the editor with a valid token and an ordinary "save as" name, and
subscribing to one's own folder's activity) must continue to work. There is no
network access at test time; the server runs entirely against its local backend.
