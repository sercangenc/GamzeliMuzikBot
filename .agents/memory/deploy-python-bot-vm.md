---
name: Deploying the non-artifact Python bot 24/7
description: How the music bot is deployed for always-on operation in this pnpm-workspace repl, and the deps gotcha.
---

This repl is a `PNPM_WORKSPACE` stack, so **publishing is artifact-based**: the Publish flow only unlocks when a **deployable app artifact** exists (kind `web` / `expo` / `data-visualization`). `api` and `design` kinds do NOT open the publish gate → "There's nothing to publish yet". The `.replit [deployment].run` command is IGNORED in this stack.

**`kind` is immutable:** `verifyAndReplaceArtifactToml` rejects any change to an artifact's `kind` ("cannot change artifact kind"). So you cannot convert the existing `api` server into a `web` app — you must create a separate `web` artifact to open the publish gate.

**Working approach (two artifacts deploy together):**
- A `web` artifact (here `artifacts/muzik-botu`, previewPath `/`): a simple status/commands page. Its only job is to be the deployable app that unlocks Publish. Served statically (vite build) by the router.
- The `api` server artifact (`artifacts/api-server`, paths `/api`) runs the bot: its `artifact.toml` `[services.production.run]` runs both processes via `["sh","-c","node --enable-source-maps artifacts/api-server/dist/index.mjs & cd music-bot && exec python bot.py"]`. The Node server keeps the `/api/healthz` health check green; the bot runs as the foreground process. Only `[services.production]` is changed — dev workflows are untouched.
- `router = "application"` makes ALL artifact production services run together on the same deploy, so the web "/" page and the api-server bot both run on one VM.
- Edit `artifact.toml` only via `verifyAndReplaceArtifactToml` (temp file + callback), never directly. Edit `.replit` only via `verifyAndReplaceDotReplit`. `router = "application"` must stay or publish detection breaks.

**Why VM, not autoscale:** the bot holds a persistent MTProto connection and `idle()`s forever; autoscale scales to zero, so it would never stay alive. User must pick the Reserved VM option in the Publish UI.

**Deps gotcha (production install):** the bot's Python deps must live in the repl-root `pyproject.toml` (installed via `installLanguagePackages` → uv, which writes `uv.lock`). `music-bot/requirements.txt` is NOT read by Replit's deployment build → `ModuleNotFoundError` in production if deps only live there. Pin versions to the working dev set.

**Also required in production:** ffmpeg (in `replit.nix`) and the Telegram secrets (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING`).

**How to apply:** dev environment sleeping/closing stops the workflow-run bot; only a published VM deployment runs 24/7.
