# yt-dlp creates files whose type the remote site chooses

yt-dlp is a command-line audio/video downloader and a Python library. The user chooses an output
template (`-o`) and a download folder; yt-dlp fills the template with metadata returned by the
remote site and downloads the media into that folder.

## Impact

A page can make yt-dlp create a file of a type it would never produce for that download. A page
that advertises its media as a Windows executable is saved as `ffmpeg.exe` instead of a video;
because `ffmpeg.exe` is looked up in the working directory, a later run can execute the attacker's
file.

## Required properties

No value supplied by the remote site may decide the type of a file yt-dlp creates. A download must
never produce an executable, script, shortcut or configuration file because the site chose that
type, however the site supplies it.

No value supplied by the remote site may cause a file to be created or changed outside the folder
the user chose for the download.

## Contracts

- When yt-dlp refuses such a download it reports an error and leaves the filesystem as it found it:
  no file and no directory is created or changed.
- Everything that works today keeps working exactly as today.
- These examples are examples, not the full set.

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example.
