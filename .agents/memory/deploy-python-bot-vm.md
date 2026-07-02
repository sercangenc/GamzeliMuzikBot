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

**ffmpeg MUST be declared in `replit.nix` — the dev runtime-path is a lie for production.** In dev, `which ffmpeg` resolves via `.../replit-runtime-path/bin/ffmpeg` even with no `replit.nix`, so it looks installed. Production does NOT get that path; if ffmpeg is only there, the download reaches ~100% then the `FFmpegExtractAudio` (mp3) postprocessor fails silently → no mp3 file → `download_audio` returns None → bot replies "❌ Şarkı bulunamadı veya indirilemedi." Symptom to recognize: yt-dlp download progress appears in logs but no completion/mp3, and the user gets "not found". Fix: `installSystemDependencies(["ffmpeg"])` (writes `pkgs.ffmpeg` into `replit.nix`). **Why:** the postprocessor error is swallowed by `except Exception` + buffered `print`, so it never surfaces.

**Production diagnosability — run Python unbuffered.** bot.py/downloader.py use bare `print()`; in the deployed VM stdout is block-buffered, so success/error prints (e.g. `[downloader] Hata: ...`) never appear in deployment logs and failures look like silence. Fix applied: production run uses `python -u bot.py` and `[services.production.run.env] PYTHONUNBUFFERED = "1"`. Pyrogram/PyTgCalls errors go to stderr and show regardless; the app's own `print()` diagnostics do NOT without this.

**yt-dlp JS runtime is NOT required for basic audio downloads.** yt-dlp 2026.06.09 warns "No supported JavaScript runtime could be found" and marks nix `deno` 2.2.12 as `(unsupported)`, but extraction falls back to the android/android-vr player client and still yields playable formats — end-to-end mp3 downloads succeed without any JS runtime. Do not chase the JS-runtime warning as the cause of "song not found"; check ffmpeg first. (deno is left in `replit.nix` as harmless future-proofing.)

**How to apply:** dev environment sleeping/closing stops the workflow-run bot; only a published VM deployment runs 24/7.

**Recovery/checkpoint can silently reset `.replit` — verify before every publish.** A "Post-Recovery checkpoint" was observed to (a) drop `python-3.11` from `modules` (leaving only `["nodejs-24"]`) and (b) flip `deploymentTarget` from `vm` back to `autoscale`. Symptom: production logs show `sh: 1: exec: python: not found` (bot never starts, only the Node health server runs). Fix: reinstall the module with `installProgrammingLanguage("python-3.11")` (restores the modules line + `which python`), then set `deploymentTarget = "vm"` via `verifyAndReplaceDotReplit`. **Why:** without Python the bot binary is missing; autoscale scales the always-on MTProto bot to zero. `verifyAndReplaceDotReplit` needs an ABSOLUTE tempFilePath INSIDE the workspace (e.g. `/home/runner/workspace/.local/...`), not `/tmp` and not a relative path.
