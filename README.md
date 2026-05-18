# premiere-session-bootstrap

Premiere Pro automation experiments for the piano multicam workflow.

This repository exists to answer one practical question:

> If editing returns from DaVinci Resolve to Adobe Premiere Pro, which parts of
> the current `davinci-session-bootstrap` workflow can still be automated?

Current answer:

- Keep automation for ingest, take grouping, validation, still/contact-sheet
  review, and operator handoff.
- Premiere can be automated for bins, importing media, and project/sequence
  setup.
- Sound-synced multicam source sequence creation and "use only the external
  AIF audio as final audio" need direct Premiere API verification. Manual
  Premiere UI supports the workflow, but public scripting APIs are not as clear
  as Resolve's Python API for this exact task.

## Initial Verdict

| Task | Likely automation path | Confidence |
| --- | --- | --- |
| Read grouped `session.yaml` / `take.yaml` | Python CLI | High |
| Write Premiere operator manifest | Python CLI | High |
| Create Premiere bin structure | ExtendScript or UXP | High |
| Import grouped media | ExtendScript `importFiles` or UXP media import | High |
| Create ordinary sequences | ExtendScript or UXP | Medium |
| Create sound-synced multicam source sequence | Needs local Premiere verification | Low/Unknown |
| Force final audio to external AIF only | Likely partly automatable after multicam exists | Medium/Unknown |
| Apply Lumetri presets per angle | Possible via presets/effects, needs verification | Medium |
| Export YouTube SDR | Possible, but profile/preset-driven | Medium |

## Why This Is Separate From the DaVinci Repo

`davinci-session-bootstrap` has been refocused on Resolve Stage A/B and manual
Resolve handoff. This repo is the Premiere branch of the investigation so the
two directions can evolve independently.

## CLI

Generate a Premiere-facing manifest and handoff from a grouped session:

```bash
python -m premiere_session_bootstrap premiere-manifest /path/to/session --json
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
```

## Probe Scripts

This machine currently does not have Adobe Premiere Pro installed under
`/Applications`, so the repository includes probe scripts to run on a Premiere
machine.

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
`premiere-manifest.json` into take bins. It is intentionally conservative:
import/bin automation first, multicam construction later after API probing.

### UXP Probe

`uxp/premiere-bootstrap-probe/` is a minimal UXP plugin skeleton for probing the
newer Premiere Pro API surface.

## Recommended Premiere Workflow If Returning From Resolve

1. Use `davinci-session-bootstrap` or this repo's future common ingest path to
   group `/incoming/` into `takes/`.
2. Generate `premiere-manifest.json`.
3. In Premiere, import each take into bins.
4. For each take, create a multicam source sequence using audio sync.
5. Keep camera scratch audio only for sync; disable/mute it after sync.
6. Use the external AIF/WAV as the final audio source.
7. Edit with Premiere multicam tools.
8. Use Lumetri/presets for angle/take color.
9. Export YouTube SDR.

## Current Open Questions

- Can UXP create a multicam source sequence with audio sync directly?
- Can ExtendScript access the same command without fragile UI scripting?
- After multicam creation, can scripting programmatically switch the audio
  mapping to external AIF only?
- Is a preset-driven Lumetri workflow good enough for this piano material?

