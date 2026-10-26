# PrivateBin — a paste attachment must not become a page

PrivateBin is a self-hosted paste service whose content is encrypted in the browser before it is
stored. A paste may carry one file attachment; when a visitor opens such a paste, the attachment
is decrypted in the page and offered through a "Download attachment" link, and some kinds of
attachment are previewed inline.

An attacker can create a paste whose attachment declares itself as a web page (an HTML or SVG
file, say). When the visitor opens the paste and then opens the attachment, the attacker's content
is treated as a document of the PrivateBin origin, so the script it contains runs with access to
that origin. The instance's content security policy must not be relied on to stop this.

## Required property

No content that a paste carries as an attachment may be rendered or opened as a document in the
PrivateBin origin. Attachment content may be shown only when its own declared kind is one that is
safe to display; content of every other kind must only ever be offered for download.

Every attachment that a paste carries must be offered as a download: using its attachment link
saves the file and never opens the payload as a page.

## Behaviour that must not change

Everything that works correctly today keeps working exactly as today, apart from the properties
above: previews that are available today stay available, attachments of every kind keep
downloading with their original content, and attachment names keep being shown and used as file
names exactly as they are, including non-ASCII text and characters such as quotes and ampersands.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
