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

Local probe target:

```text
Adobe Premiere Pro 2026
Version observed in UXP logs: 26.2.2
macOS host: Apple Silicon
```

The current safe boundary is:

```text
Scriptable:
  - Read grouped session metadata.
  - Generate Premiere manifest and handoff.
  - Create/import bin-oriented project structure.
  - Import all take media.

Needs local Premiere API probe:
  - ExtendScript/QE access to Create Multi-Camera Source Sequence.
  - Programmatically choose external AIF/WAV as final audio only after multicam creation.
  - Apply Lumetri presets robustly per angle/take.
```

Checked and not found in the public UXP 26.2 type definitions:

```text
  - create multicam source sequence
  - synchronize by audio
  - multicam audio source/routing setup
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
  scripting API or only through unsupported/private QE internals.
- Whether audio-sync options can be set without UI automation.
- Whether the resulting multicam source sequence's audio routing can be edited
  cleanly so only external AIF/WAV remains audible.

Local command-line attempt:

```bash
Adobe\ Premiere\ Pro\ 2026 /C es.processFile /tmp/premiere-codex-probe.jsx
```

On this machine that path spawned a second Premiere process and crashed/hung
without writing the probe JSON. Do not use this as the normal runner for
Premiere 2026 on this Mac.

## UXP

UXP is Adobe's newer extension platform. Adobe publishes Premiere UXP type
definitions on npm. The installed app is 26.2.2, so `@adobe/premierepro@26.2.0`
was inspected locally.

Confirmed public UXP capabilities include:

- `Project.createProject()`
- `Project.open()`
- `Project.importFiles()`
- `Project.createSequence()`
- `Project.createSequenceFromMedia()`
- `SequenceEditor.createInsertProjectItemAction()`
- `SequenceEditor.createOverwriteItemAction()`
- `Sequence.createSetSettingsAction()`

The same type definitions include `ClipProjectItem.isMulticamClip()`, but no
public API for creating a multicam source sequence or requesting audio sync.

Use `uxp/premiere-bootstrap-probe/` as the starting point for checking available
methods in the running Premiere version.

CEP note: a user-level CEP probe was installed under
`~/Library/Application Support/Adobe/CEP/extensions`, with unsigned loading
enabled for common CSXS versions. Premiere 2026 did not log or auto-load that
extension on restart. The system-level CEP extension folder exists but is not
writable by the current shell without administrator elevation.

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

Premiere's UI supports this kind of multicam/audio-sync workflow. The current
evidence says the official UXP API does not expose it directly. The remaining
question is whether ExtendScript/QE exposes a stable enough private route; if
not, this step should stay manual.

## Current Recommendation

Start with conservative automation:

1. Generate `premiere-manifest.json`.
2. Import and organize media into Premiere bins.
3. Leave multicam source sequence creation to the operator unless an
   ExtendScript/QE probe proves otherwise.
4. Treat external-audio-only as a manual post-sync cleanup step until a stable
   API path is found.
