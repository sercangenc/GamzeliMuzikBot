---
name: Deploying the non-artifact Python bot 24/7
description: How the music bot is deployed for always-on operation in this pnpm-workspace repl, and the deps gotcha.
---

This repl is a `PNPM_WORKSPACE` stack, so **publishing is artifact-based**: the Publish flow only deploys registered artifacts via the application router, and the `.replit [deployment].run` command is IGNORED. Setting a plain `deploymentTarget="vm"` + `run=[...]` in `.replit` produces "There's nothing to publish yet" because the bot is not an artifact.

**Working approach:** host the bot inside an existing artifact's production run command.
- `.replit [deployment]` (via `verifyAndReplaceDotReplit`): `router = "application"` + `deploymentTarget = "vm"` (keep `postBuild` pnpm store prune). Removing `router` breaks publish detection.
- The api-server artifact (an unused stub) is repurposed: its `artifact.toml` `[services.production.run]` runs both processes via `["sh","-c","node --enable-source-maps artifacts/api-server/dist/index.mjs & cd music-bot && exec python bot.py"]`. The Node server keeps the `/api/healthz` health check green (so the VM stays healthy); the bot runs as the foreground process. Only `[services.production]` is changed — dev workflows are untouched.
- Edit artifact.toml only via `verifyAndReplaceArtifactToml` (temp file + callback), never directly.

**Why VM, not autoscale:** the bot holds a persistent MTProto connection and `idle()`s forever; autoscale scales to zero, so it would never stay alive.

**Deps gotcha (production install):** the bot's Python deps must live in the repl-root `pyproject.toml` (installed via `installLanguagePackages` → uv, which writes `uv.lock`). `music-bot/requirements.txt` is NOT read by Replit's deployment build → `ModuleNotFoundError` in production if deps only live there. Pin versions to the working dev set.

**Also required in production:** ffmpeg (in `replit.nix`) and the Telegram secrets (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING`).

**How to apply:** dev environment sleeping/closing stops the workflow-run bot; only a published VM deployment runs 24/7. User must click Publish and pick the Reserved VM option.
