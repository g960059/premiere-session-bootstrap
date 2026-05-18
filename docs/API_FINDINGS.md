# Premiere Pro API Findings

Date: 2026-05-18

## Sources Checked

- Adobe Premiere Pro Scripting Guide:
  <https://ppro-scripting.docsforadobe.dev/>
- Adobe Premiere Pro UXP API:
  <https://developer.adobe.com/premiere-pro/uxp/>
- Adobe help page for creating multicamera source sequences:
  <https://helpx.adobe.com/premiere-pro/using/create-multi-camera-source-sequence.html>

## Practical Summary

Premiere Pro has scriptable APIs, but the exact workflow needed here is split
between clearly scriptable project setup and unclear multicam automation.

The current safe boundary:

```text
Scriptable:
  - Read grouped session metadata.
  - Generate Premiere manifest and handoff.
  - Create/import bin-oriented project structure.
  - Import all take media.

Needs local Premiere API probe:
  - Create multicam source sequence with audio sync.
  - Programmatically choose external AIF/WAV as final audio only.
  - Apply Lumetri presets robustly per angle/take.
```

## ExtendScript

The legacy ExtendScript API is broad and mature enough for project-oriented
tasks. It should be able to:

- Create bins.
- Import files.
- Traverse project items.
- Create or manipulate ordinary sequences.

Open questions:

- Whether `Create Multi-Camera Source Sequence` is directly exposed as a stable
  scripting API.
- Whether audio-sync options can be set without UI automation.
- Whether the resulting multicam source sequence's audio routing can be edited
  cleanly so only external AIF/WAV remains audible.

## UXP

UXP is Adobe's newer extension platform. It may expose newer Premiere APIs, but
the multicam/audio-sync workflow still needs hands-on probing in a machine with
Premiere installed.

Use `uxp/premiere-bootstrap-probe/` as the starting point for checking available
methods in the running Premiere version.

## Multicam + External AIF Requirement

Desired workflow:

```text
Per take:
  camera angle MP4s + external audio.aif
    -> multicam source sequence
    -> synchronization by audio
    -> camera scratch audio disabled/muted
    -> external AIF/WAV is the only final audio
```

Premiere's UI supports this kind of multicam/audio-sync workflow. The remaining
question is whether it can be automated via official scripting/UXP APIs without
fragile UI scripting.

## Current Recommendation

Start with conservative automation:

1. Generate `premiere-manifest.json`.
2. Import and organize media into Premiere bins.
3. Leave multicam source sequence creation to the operator until a probe proves
   otherwise.
4. If a stable API path is found, add an automation layer that creates one
   multicam source sequence per take and applies the external-audio-only policy.

