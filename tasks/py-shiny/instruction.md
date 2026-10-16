# Bookmark restore can be steered to read files outside the bookmark store

## Summary

This web framework offers a "bookmarking" feature. When an application is
configured with server-side bookmarking, the running state of a user's session
is written to a per-bookmark subdirectory inside a store folder (named
`shiny_bookmarks`) under the application's working directory. Each bookmark is
identified by a short id, and that id is echoed back to the client as a query
string parameter (`_state_id_`) in the shareable bookmark URL.

When a client later opens a bookmark URL, the server restores that saved state:
on the initial `GET /` request it reads the saved state for the requested
bookmark id and uses it to repopulate the application's inputs, which are then
rendered into the returned HTML page.

The bookmark id taken from the request is used to build the filesystem path of
the directory to read **without being validated as a safe, single path
segment**. A client can therefore supply an id that is not a plain name but a
relative or absolute path. The server joins it to the store location and reads
state from the resulting directory, which can lie **anywhere on the server's
filesystem, outside the bookmark store**. The attacker chooses the directory,
so any state the server finds there (for example a planted `input.json`) is
loaded and reflected back into the page the victim receives.

## How it is triggered

An application running with server-side bookmarking is reachable at
`http://host/`. Instead of a normal bookmark id such as `a1b2c3`, the attacker
requests the root URL with a bookmark id whose value walks out of the store,
for example:

```
GET /?_state_id_=../../some/other/directory
```

The leading segments climb out of `shiny_bookmarks`, and the server reads saved
state from the attacker-named directory rather than from a real bookmark. The
same outcome is reachable through other spellings of an out-of-store location,
including percent-encoded separators, deeper or mixed relative paths, and an
absolute path supplied as the id. In each case the restored values appear in
the HTML of the response, confirming that the out-of-store location was read.

## What a correct fix must achieve

- A client-supplied bookmark id must only ever address a location **inside the
  intended bookmark store**. No value of the id — whatever separators,
  relative segments, encodings, or absolute form it uses — may cause the
  server to read saved state from a directory outside that store. Blocking one
  obvious spelling of the attack while leaving others working is not a fix.
- Legitimate bookmarking must keep working. A genuine, well-formed bookmark id
  (letters, digits, and the kinds of characters used by generated ids) must
  still restore the state saved under it, and the restored input values must
  still appear in the rendered page. Applications that restore state encoded
  directly in the query string, rather than from a saved id, must be
  unaffected. A fix that disables or broadly curtails bookmark restore is not
  acceptable.

## Environment

Pure Python; no external services to start. The framework is installed in
editable mode, so edits under the source tree take effect immediately. The
tests drive the application the way a browser would: an in-process HTTP client
issues `GET /` requests to a small app configured with server-side bookmarking
and inspects the returned HTML.
