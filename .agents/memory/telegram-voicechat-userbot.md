---
name: Telegram voice chat requires a user account, not a bot
description: Why a Telegram music/voice-streaming bot needs an "assistant" userbot session in addition to the bot token.
---

# Telegram bots cannot join voice chats

Telegram blocks bot accounts from joining or creating group voice chats. Calling `phone.CreateGroupCall` / joining a group call with a bot token fails with:
`[400 BOT_METHOD_INVALID] ... The method can't be used by bots`.

**Why:** Voice chat (group call) streaming is only permitted for real user accounts at the MTProto level. This is a Telegram-side restriction, not a library limitation.

**How to apply:** A music/voice-streaming bot needs TWO clients:
1. **Bot client** (bot_token) — handles commands (`/play`, `/skip`, ...) and replies in chat.
2. **Assistant client** — a real user account, authenticated via a Pyrogram/pyrofork **session string** (generated from a phone-number login). `PyTgCalls(assistant)` must wrap the assistant, NOT the bot.

The assistant account must also be a **member of the group** to join its voice chat (auto-join via invite link, or add it manually). Session string is stored as the `TELEGRAM_SESSION_STRING` secret; generate it with an interactive `export_session_string()` script run in the Shell (cannot be done non-interactively because it needs phone + OTP + optional 2FA).

## Gotchas for PyTgCalls music bots

- **Queue mutations need a per-chat `asyncio.Lock`.** `StreamEnded`, `/skip`, `/stop`, and `/play` all mutate the same per-chat queue. Without a lock, `StreamEnded` firing while `/skip` runs causes a **double-pop** (the next track gets skipped too). The internal "play next or leave" function must be called while holding the lock and must NOT re-acquire it — `asyncio.Lock` is non-reentrant, so re-acquiring deadlocks.
  **Why:** advancement is triggered both by the user and by the stream-ended event, so two code paths race on the same deque.

- **Always pass `in_memory=True` to both Pyrogram clients.** Otherwise Pyrogram writes a `<name>.session` SQLite file to disk — these are **credentials** and must never land in the repo. The bot token client and the assistant (session-string) client both already carry their auth inline, so no session file is needed. Also gitignore `*.session` and the downloads dir.

- **Clean up downloaded audio files.** `downloads/` is never auto-purged. Delete each track's file after it finishes/skips/stops/fails, purge leftover/`.part` files of a failed download by uid prefix, and `clear_downloads()` on startup + shutdown — otherwise disk fills up on a long-running bot.
