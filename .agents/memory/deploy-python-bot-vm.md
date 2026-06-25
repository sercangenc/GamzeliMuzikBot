---
name: Deploying the non-artifact Python bot 24/7
description: How the music bot is deployed for always-on operation in this pnpm-workspace repl, and the deps gotcha.
---

The music bot is a standalone Python background process (not a registered artifact), so it deploys via the repl-level `[deployment]` block, NOT via any `artifact.toml`.

Config (set with the `verifyAndReplaceDotReplit` callback — direct edits to `.replit` are blocked):
- `deploymentTarget = "vm"` (always-on Reserved VM; a background worker has no HTTP/port).
- `run = ["sh", "-c", "cd music-bot && python bot.py"]`.
- Remove `router = "application"` and the pnpm `postBuild` — those are for the web artifacts, not the bot.

**Why VM, not autoscale:** A Telegram bot holds a persistent MTProto connection and `idle()`s forever. Autoscale scales to zero / expects HTTP health checks, so it would never keep the bot alive.

**Deps gotcha (production install):** The bot's Python deps must live in the repl-root `pyproject.toml` (installed via `installLanguagePackages` → uv, which also writes `uv.lock`). `music-bot/requirements.txt` is NOT read by Replit's deployment build, so deps only there → `ModuleNotFoundError` in production. Pin versions to match the working dev set to avoid drift.

**Also required in production:** ffmpeg (already in `replit.nix`) and the Telegram secrets (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING`).

**How to apply:** Dev environment sleeping/closing stops the workflow-run bot; only a published VM deployment runs 24/7. User must click Publish and pick the Reserved VM option.
