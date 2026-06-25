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

- **Never start pyrofork/PyTgCalls clients with `asyncio.run()` when clients are created at module import.** Pyrogram (`Client`) and PyTgCalls both capture the event loop with `asyncio.get_event_loop()` in their `__init__`. Module-level client creation captures loop A; `asyncio.run(main())` then makes a NEW loop B and runs `main()` there. The bot's dispatcher `handler_worker` stays bound to loop A (never driven) so the **bot silently receives ZERO updates** — commands get no response, no error logged. Tell-tale sign on shutdown: `RuntimeError: ... got Future ... attached to a different loop`. **Fix:** before creating any client, do `loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)`, then run with `loop.run_until_complete(main())` — so the captured loop and the run loop are the same one. PyTgCalls also schedules `StreamEnded`/connection callbacks via `run_coroutine_threadsafe(..., self.loop)`, so they only fire when this is correct.
  **Why:** the failure is invisible (connects fine, getMe works, just no updates), so it looks like a token/permission/webhook problem and wastes hours. Diagnosed by having the assistant send a test message to the group and confirming a catch-all bot handler logged 0 vs 1.

- **PyTgCalls (py-tgcalls v2.3.x) has no `stop()` method.** `call_py.start()` internally starts the wrapped assistant client (`self._app.start()`). To shut down, call `await assistant.stop()` on the underlying client — `await call_py.stop()` raises `AttributeError`.

- **Turkish-speaking users type Turkish command names.** Telegram only auto-suggests ASCII commands, but users still type `/oynat`, `/atla`, `/durdur`, etc. Register aliases via `filters.command(["play", "oynat", "çal", "cal"])` (include ASCII fallbacks like `cal`/`gec` alongside `çal`/`geç`).
