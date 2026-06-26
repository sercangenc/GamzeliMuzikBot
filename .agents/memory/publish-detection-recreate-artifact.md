---
name: Publish "nothing to publish" despite a web artifact
description: When the Publish UI says there's nothing to deploy even though a deployable web artifact exists and runs, recreate the artifact to re-register it.
---

If the Publish UI shows "There's nothing to publish yet — only design mockups and reusable libraries" even though a valid deployable web artifact (kind=web/expo/data-visualization) exists, runs in dev, and shows in `listArtifacts()`, the artifact is registered for preview/workflow but NOT in the deployment-eligible manifest.

**Fix:** back up custom source files, `rm -rf artifacts/<slug>`, then recreate with `createArtifact()`. The full bootstrap flow re-registers it so the Publish scanner detects it. After recreation, restore your custom source (the scaffold overwrites `src/App.tsx` etc.).

**Why:** an artifact created/edited outside the normal `createArtifact()` flow (e.g. directory + artifact.toml written manually in a prior session) can land in a half-registered state. The `artifactId` string being a path like `artifacts/<slug>` is NORMAL for this stack and is NOT the cause — recreation produces the same id but fixes the registration.

**How to apply:** verify with `getDeploymentInfo()` (a stale/failed prior deployment shows `hasSuccessfulBuild:false`); recreate the artifact; confirm publish succeeds and `hasSuccessfulBuild` flips to true.
