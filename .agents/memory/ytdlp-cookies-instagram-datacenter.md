---
name: yt-dlp cookies & Instagram from datacenter IP
description: Why browser cookie exports lack auth, and why Instagram is unreliable even with valid cookies on server IPs
---

## Browser cookie-export extensions often drop the auth session
- "Get cookies.txt LOCALLY" and similar extensions frequently export only NON-HttpOnly cookies. The login cookies are HttpOnly and get skipped:
  - Instagram auth cookie = `sessionid` (also `ds_user_id`).
  - YouTube auth cookie = `LOGIN_INFO` (and `__Secure-1PSID/3PSID`).
- Symptom: exported file looks populated (csrftoken, mid, VISITOR_INFO1_LIVE, YSC, PREF...) but yt-dlp still says "Sign in" / "empty media response". Verify by grepping the file for `sessionid` / `LOGIN_INFO` — if absent, it is NOT a logged-in export.
- **Reliable method:** `yt-dlp --cookies-from-browser firefox --cookies cookies.txt --skip-download <url>` reads the browser cookie DB directly (includes HttpOnly).
  - **Chrome 127+ breaks `--cookies-from-browser`** (App-Bound Encryption → empty). Use Firefox.

## Instagram is intermittent from Replit datacenter IPs EVEN WITH a valid login cookie
- **Why:** With a valid `sessionid`, the same reel resolved successfully on one attempt and returned "Instagram sent an empty media response" on the very next attempt (same cookie file). This is Instagram throttling/blocking datacenter IPs, not a code bug.
- **How to apply:** Do NOT chase Instagram "empty media response" as a downloader bug once you've confirmed the cookie has `sessionid` and worked at least once. It will work sometimes, fail often. Set user expectations accordingly. TikTok / YouTube-search / most links work reliably; YouTube logged-in content needs `LOGIN_INFO` cookies (separate export).
- Using a real Instagram session on a server also risks the account being flagged — warn the user.

## Applying an updated YTDLP_COOKIES secret in production
- `downloader._ensure_cookies()` writes `music-bot/cookies.txt` from the `YTDLP_COOKIES` env at import (bot startup). A running production VM keeps the OLD cookie until redeploy — user must Publish again to apply an updated cookie.
