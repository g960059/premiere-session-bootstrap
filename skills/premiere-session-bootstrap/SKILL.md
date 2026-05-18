---
name: premiere-session-bootstrap
description: |
  Premiere-first piano multicam bootstrap: auto-group incoming camera videos
  and external audio into takes, generate Premiere project/import handoff files,
  and stop before manual Premiere multicam creation.
disable-model-invocation: true
---

# premiere-session-bootstrap

Use this skill for the Premiere Pro version of the piano multicam workflow.
It is self-contained and must not call `davinci-session-bootstrap`.

Default behavior stops at a Premiere-ready handoff:

1. **group-session**: `<session-root>/incoming/` media -> `takes/take-XX/`.
2. **premiere-manifest**: write Premiere manifest, handoff, import JSX, and
   runbook.
3. **run-premiere-import**: ask Premiere Pro to run the generated import JSX,
   then verify `reports/premiere-import-result.json`.
4. **Premiere manual step**: create one audio-synced multicam source sequence
   per take in Premiere's UI.

## Prerequisites

Halt and surface the issue on any failure.

1. `<session-root>/incoming/` exists and contains camera videos plus one or more
   audio files (`.wav`, `.aif`, `.aiff`, or `.flac`) for grouping, or the
   session is already grouped under `takes/`.
2. `ffmpeg` and `ffprobe` are available on PATH.
3. `${CLAUDE_SKILL_DIR}/.venv/bin/premiere-session-bootstrap` exists. If
   missing, ask the operator to run `${CLAUDE_SKILL_DIR}/scripts/install.sh`.

Always invoke the CLI via:

```bash
${CLAUDE_SKILL_DIR}/scripts/psb
```

## One-Shot Bootstrap

For a normal session, run:

```bash
${CLAUDE_SKILL_DIR}/scripts/psb bootstrap-session "<session-root>" --json
${CLAUDE_SKILL_DIR}/scripts/psb run-premiere-import "<session-root>" --json
```

This groups media if `incoming/` still contains source files, then writes:

- `<session-root>/session.yaml`
- `<session-root>/takes/take-XX/take.yaml`
- `<session-root>/reports/auto-group-plan.json`
- `<session-root>/reports/auto-group-apply.json`
- `<session-root>/reports/premiere-manifest.json`
- `<session-root>/reports/premiere-handoff.md`
- `<session-root>/reports/premiere-bootstrap-import.jsx`
- `<session-root>/reports/premiere-import-runbook.md`
- `<session-root>/reports/premiere-import-result.json` after
  `run-premiere-import` succeeds.

Use `--project-path` when the Premiere project should be created somewhere
other than `<session-root>/<session-id>.prproj`.

## Separate Stages

When debugging grouping, split the workflow:

```bash
${CLAUDE_SKILL_DIR}/scripts/psb group-session "<session-root>" --dry-run --json
${CLAUDE_SKILL_DIR}/scripts/psb group-session "<session-root>" --json
${CLAUDE_SKILL_DIR}/scripts/psb premiere-manifest "<session-root>" --json
${CLAUDE_SKILL_DIR}/scripts/psb run-premiere-import "<session-root>" --json
```

- Use only `<session-root>/incoming/` by default.
- Do not look for `<session-root>/incomings/` unless the operator explicitly
  passes `--incoming-dir`.
- If grouping returns `FAIL`, stop. Do not guess a take layout.

## Premiere Import

After `premiere-manifest`, prefer the CLI runner:

```bash
${CLAUDE_SKILL_DIR}/scripts/psb run-premiere-import "<session-root>" --json
```

The script creates/opens the `.prproj`, creates take bins, imports angle videos
and the final external audio, saves the project, and writes:

```text
<session-root>/reports/premiere-import-result.json
```

Treat the runner as successful only when that result JSON exists and reports
`status: PASS`. If the runner returns `FAIL`, surface the failure, the stderr
log path, and tell the operator to run
`<session-root>/reports/premiere-bootstrap-import.jsx` manually from a Premiere
ExtendScript environment.

If the CEP panel is available, `Window > Extensions > Premiere Bootstrap` can
run the same import flow through `Import Session Manifest`.

## Manual Premiere Multicam Step

For each take bin:

1. Select all angle videos and the final external audio.
2. Right-click -> `Create Multi-Camera Source Sequence...`.
3. Set Synchronize Point to `Audio`.
4. Use camera audio only for synchronization.
5. Name the source sequence `MC_take-XX`.
6. After creation, mute/disable camera scratch audio.
7. Keep `audio.aif` or `audio-edit.wav` as the only final audio.

Do not claim that audio-synced multicam creation is automated. Adobe's public
Premiere UXP 26.2 API exposes import and ordinary sequence operations, but no
public audio-synced multicam creation API.

## Completion Message

```text
Premiere bootstrap complete.
  Takes: <N>
  Manifest: <session-root>/reports/premiere-manifest.json
  Import JSX: <session-root>/reports/premiere-bootstrap-import.jsx
  Import result: <session-root>/reports/premiere-import-result.json
  Runbook: <session-root>/reports/premiere-import-runbook.md

Next step: in Premiere, create one audio-synced multicam source sequence per
take.
```
