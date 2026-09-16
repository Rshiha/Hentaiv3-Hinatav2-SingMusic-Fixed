# InstaGoat-Py — Hinatav2-style Instagram bot

Python/instagrapi implementation with the requested Hinatav2-style command layer.

## Main commands

- `.music <song>` / `.music 1`
- `.sing <song>` / `.sing 1`
- `.anisearch <anime>`
- `.img <image-url>`
- `.ai <question>`
- `.aiimg <prompt>`
- `.avatarfx <love|angry|laugh|cry> <text>`
- `.effect <love|gift|celebration|fire> <text>`
- `.bio <text>` (admin)
- `.avatar <image-url>` (admin)
- `.ban <user-id>` / `.unban <user-id>` (admin)
- `.removeuser <user-id>` (admin/group only)
- `.whitelist on|off|list|add|remove` (admin)

The music flow searches JioSaavn first and uses YouTube search to fill missing results. Selecting a number downloads the selected track and sends it as playable media. `ffmpeg` is installed in the Docker image because Instagram DM audio is converted to a playable MP4 when necessary.

## Render environment

Set at least:

- `IG_SESSIONID` — Instagram session id
- `IG_ADMIN_BOT` — comma-separated Instagram numeric user IDs allowed to use admin commands
- optional `YTDLP_COOKIES` — path to a cookies.txt file for yt-dlp where needed
- optional `POLL_INTERVAL` — DM polling interval in seconds

Do not commit session IDs, cookies, passwords, or API tokens to GitHub.
