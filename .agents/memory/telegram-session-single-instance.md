---
name: Telegram assistant session — single instance only
description: One Telegram user (assistant) session string cannot run in two places at once; running dev + production simultaneously crashes both with AUTH_KEY_DUPLICATED.
---

A single Telegram **user account** session (`TELEGRAM_SESSION_STRING`, used by the assistant client / py-tgcalls) can only be connected in ONE place at a time. If the same session string is used by two running processes simultaneously, Telegram rejects BOTH with:

`406 AUTH_KEY_DUPLICATED ... The same authorization key (session file) was used in more than one place simultaneously.`

**Why it bit us:** the dev workflow that ran `python bot.py` AND the published VM deployment (which also runs `python bot.py` via the api-server production process) were both live at the same time → both crashed on `call_py.start()`.

**How to apply:**
- For a 24/7 published bot, the bot must run ONLY in the production VM. Do NOT keep a dev workflow that auto-runs `bot.py` — it auto-starts whenever the repl boots and re-breaks production. (The dev "Telegram Müzik Botu" workflow was removed for this reason.)
- To test the bot in dev, production must be stopped first (or use a separate assistant account/session) — never both at once.
- AUTH_KEY_DUPLICATED is usually transient: once only one instance connects, reconnect works without regenerating. If it persists after ensuring a single instance, regenerate the session with `music-bot/generate_session.py` and update the secret.
