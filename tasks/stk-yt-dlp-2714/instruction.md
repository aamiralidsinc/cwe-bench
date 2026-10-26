# A downloaded video can be saved as a launcher or shortcut file

yt-dlp names the files it writes from the information it receives about a video. Desktop
environments treat three filename suffixes as programs or shortcuts rather than as data:
`url`, `desktop` and `webloc`. A video site reported one of those as the video's file type,
and the download was saved as `Title [id].desktop`; the user's desktop then offered to open
or run it.

## Security invariant

No file written by yt-dlp may carry the suffix `url`, `desktop` or `webloc` when that suffix
came from the information it is given about a download.

## Refusal

Refuse the download with the library's existing download error, and do not write a file that
carries the refused suffix.

## What must keep working

Everything that works today keeps working exactly as it does today.

The example above is an example, not the full set.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
