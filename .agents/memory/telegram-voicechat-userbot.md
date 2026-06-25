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
