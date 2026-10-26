# stk-privatebin-ghsaf2xf-control

Control task for `stk-privatebin-ghsaf2xf`. Same pinned checkout, same `instruction.md` (byte
identical), but only the advisory's own route (the attachment's declared media type reaching the
browser as the link/preview target) is tested and fixed. It isolates the effect of stacking from
the effect of the host.

Scope: GHSA-cqcc-mm6x-vmvw (SVG preview) and GHSA-f2xf-7x3g-4272 (download link) at PrivateBin
6c1f0dde. The control reference fixes the media-type decision and keeps the SVG preview sanitised;
it intentionally leaves the unnamed-attachment download offer and the editor-preview dispatch
untouched, because those are the stacked task's hidden levers.
