---
name: Telegram bot non-command message handling
description: Why plain-text/link handlers on a Telegram BOT need BotFather privacy off, and Pyrogram handler-ordering rules that keep a catch-all from swallowing commands.
---

# Handling non-command group messages on a Telegram bot

Context: feature where the bot auto-detects video/reels links (Instagram, TikTok, YouTube, X, etc.) pasted in a group and plays them without `/play`.

## BotFather privacy mode is the real gatekeeper
A Telegram BOT with default **privacy mode ON** only receives group messages that are commands (`/...`) or replies/@mentions to it. Plain text messages (e.g. a bare link) are NOT delivered to the bot at all — so a `filters.text` handler will silently never fire.
**How to apply:** to receive arbitrary group messages you MUST turn privacy OFF in @BotFather → `/setprivacy` → pick the bot → **Disable**. No code change enables this; it is a BotFather account setting. `/play <link>` keeps working regardless because it's a command. If auto-detection "does nothing" in production, check privacy mode first.
**Alternative (not used here):** register the listener on the *assistant user client* instead of the bot — user accounts have no privacy restriction and see every message — but then replies come from the user account, mixing UX.

## Pyrogram handler ordering — first match in a group wins
All `@app.on_message` handlers default to handler group 0. Pyrogram dispatches to the FIRST handler (in registration/file order) whose filters match, then stops propagation within that group.
**Consequence:** a broad catch-all like `@app.on_message(filters.group & filters.text)` will swallow `/skip`, `/stop`, etc. if it is registered BEFORE those command handlers.
**How to apply:** register the catch-all link/text handler LAST (after every command handler in file order), and additionally guard with `if text.startswith("/"): return`. Command handlers then win, and the guard is defense-in-depth.

## yt-dlp for social video platforms
The existing `bestaudio/best` download + the URL-extraction fallback loop already handle video-only platforms (TikTok/Instagram/etc.) — they carry a combined mp4 whose audio ffmpeg extracts. Instagram frequently needs login/cookies and fails without them; TikTok/YouTube generally work. Failures surface as the normal "İçerik bulunamadı" message via the existing download fallback.
