# premiere-session-bootstrap

Premiere Pro automation experiments for the piano multicam workflow.

This repository exists to answer one practical question:

> If editing returns from DaVinci Resolve to Adobe Premiere Pro, which parts of
> the current `davinci-session-bootstrap` workflow can still be automated?

Current answer after probing Premiere Pro 2026.2.2 on macOS:

- Keep automation for ingest, take grouping, validation, still/contact-sheet
  review, and operator handoff.
- Premiere can be automated for metadata handoff, bins, importing media, and
  ordinary project/sequence setup.
- Adobe's current UXP type definitions expose ordinary sequence creation and
  editing, but do not expose a public sound-synced multicam creation API.
- Sound-synced multicam creation and "use only the external AIF audio as final
  audio" should be treated as manual Premiere UI steps unless a future probe
  finds a reliable private/QE route worth accepting.

## Initial Verdict

| Task | Likely automation path | Confidence |
| --- | --- | --- |
| Read grouped `session.yaml` / `take.yaml` | Python CLI | High |
| Write Premiere operator manifest | Python CLI | High |
| Create Premiere bin structure | ExtendScript or UXP | High |
| Import grouped media | ExtendScript `importFiles` or UXP media import | High |
| Create ordinary sequences | ExtendScript or UXP | Medium |
| Create sound-synced multicam source sequence | Manual Premiere UI; public UXP API not found | Low |
| Force final audio to external AIF only | Manual after multicam creation, or partial sequence cleanup if exposed later | Low/Medium |
| Apply Lumetri presets per angle | Possible via presets/effects, needs verification | Medium |
| Export YouTube SDR | Possible, but profile/preset-driven | Medium |

## Why This Is Separate From the DaVinci Repo

`davinci-session-bootstrap` has been refocused on Resolve Stage A/B and manual
Resolve handoff. This repo is the Premiere branch of the investigation so the
two directions can evolve independently.

## CLI

One-shot Premiere bootstrap from `/incoming/`:

```bash
python -m premiere_session_bootstrap bootstrap-session /path/to/session --json
```

This runs grouping when incoming media exists, then writes the Premiere handoff
and import script.

Run the generated import script in Premiere Pro and verify the result:

```bash
python -m premiere_session_bootstrap run-premiere-import /path/to/session --json
```

Success requires `reports/premiere-import-result.json` with `status: PASS`.

Group only:

```bash
python -m premiere_session_bootstrap group-session /path/to/session --json
```

Generate a Premiere-facing manifest and handoff from a grouped session:

```bash
python -m premiere_session_bootstrap premiere-manifest /path/to/session --json
```

Optionally choose the `.prproj` path that the generated Premiere import script
will create/open:

```bash
python -m premiere_session_bootstrap premiere-manifest /path/to/session \
  --project-path /path/to/session/session-name.prproj
```

Expected input is the same grouped layout:

```text
<session-root>/
├── session.yaml
└── takes/
    └── take-XX/
        ├── angle-a.mp4
        ├── angle-b.mp4
        ├── angle-c.mp4
        ├── audio.aif
        └── take.yaml
```

Generated output:

```text
<session-root>/reports/premiere-manifest.json
<session-root>/reports/premiere-handoff.md
<session-root>/reports/premiere-bootstrap-import.jsx
<session-root>/reports/premiere-import-runbook.md
```

## Probe Scripts

Probe scripts are included because Premiere automation depends on what the
installed host exposes at runtime.

### ExtendScript Probe

`extendscript/probe-premiere-api.jsx` checks which Premiere scripting methods
exist in the running app.

Run it from Premiere's scripting environment or an ExtendScript-capable runner,
then inspect:

```text
~/Desktop/premiere-api-probe.json
```

### ExtendScript Import Prototype

`extendscript/import-session.jsx` imports media from a generated
`premiere-manifest.json` into take bins. The generated
`reports/premiere-bootstrap-import.jsx` is the preferred run target because it
already embeds the absolute manifest path.

The script creates/opens the project path from the manifest, creates bins,
imports only missing files, saves the project, and writes
`reports/premiere-import-result.json`. It intentionally stops before multicam
creation.

`run-premiere-import` attempts to execute that JSX through Premiere's command
line runner and treats the result JSON as the only success signal.

### UXP Probe

`uxp/premiere-bootstrap-probe/` is a minimal UXP plugin skeleton for probing the
newer Premiere Pro API surface. Use Adobe's UXP Developer Tool or Premiere's
developer-mode plugin loader to load it.

## Recommended Premiere Workflow If Returning From Resolve

1. Use this repo's `bootstrap-session` to group `/incoming/` into `takes/` and
   generate Premiere handoff files.
2. Generate `premiere-manifest.json`.
3. In Premiere, import each take into bins.
4. For each take, create a multicam source sequence using Premiere's UI audio
   sync.
5. Keep camera scratch audio only for sync; disable/mute it after sync.
6. Use the external AIF/WAV as the final audio source.
7. Edit with Premiere multicam tools.
8. Use Lumetri/presets for angle/take color.
9. Export YouTube SDR.

## Current Open Questions

- Can ExtendScript/QE access multicam creation without fragile UI scripting?
- After multicam creation, can scripting programmatically switch the audio
  mapping to external AIF only?
- Is a preset-driven Lumetri workflow good enough for this piano material?

## Codex Skill

This repo is also a self-contained Codex skill. Register it with:

```bash
ln -s /path/to/premiere-session-bootstrap/skills/premiere-session-bootstrap \
  ~/.codex/skills/premiere-session-bootstrap
```

Then ask Codex to use `premiere-session-bootstrap` for the Premiere-first piano
multicam workflow.
