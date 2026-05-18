# Premiere Piano Multicam Workflow

## 1. Shared Ingest

Use the same incoming layout as the Resolve workflow:

```text
<session-root>/
└── incoming/
    ├── camera files
    └── external audio files
```

The existing grouping logic can still be valuable even when editing in
Premiere. The desired grouped result is:

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

## 2. Premiere Manifest

Generate a Premiere handoff:

```bash
python -m premiere_session_bootstrap premiere-manifest "<session-root>" --json
```

Read:

```text
<session-root>/reports/premiere-handoff.md
```

## 3. Premiere Project Setup

In Premiere:

1. Create a project for the session.
2. Create bins:
   - `Piano Session`
   - `Piano Session/Takes`
   - `Piano Session/Takes/take-XX`
3. Import each take's angle videos and external audio into the matching bin.

This should be scriptable. The repo includes `extendscript/import-session.jsx`
as the first automation prototype.

## 4. Multicam Source Sequence Per Take

For each take:

1. Select all angle videos and the external AIF/WAV.
2. Create a multicam source sequence.
3. Synchronize using audio.
4. Use camera audio only for synchronization.
5. After sync, mute/disable camera scratch audio.
6. Keep the external AIF/WAV as the only final audio.

This is intentionally a manual Premiere UI step for now. Adobe's public UXP
26.2 API exposes normal project, import, and sequence operations, but no public
method for creating an audio-synced multicam source sequence. The repo should
therefore automate the handoff up to this point and avoid pretending this part
is reliably scriptable.

Practical Premiere settings to check while creating the multicam source:

- Synchronize Point: `Audio`
- Audio: use camera audio for synchronization only
- Final audible audio: external `audio.aif` or generated `audio-edit.wav`
- Camera scratch audio: muted/disabled after sync
- Result name: `MC_take-XX`

## 5. Editing

Assemble the piece timeline from the multicam source sequences:

```text
Piece timeline
├── MC_take-01
├── MC_take-02
└── ...
```

Use Premiere's multicam editing tools for angle switching and cutting.

## 6. Color

Premiere color workflow is expected to be simpler operationally than Resolve:

- Use Lumetri per clip/source where appropriate.
- Save angle/take corrections as presets when useful.
- Use Paste Attributes for nearby takes.
- Use adjustment layers for final global tone.

For this piano material, keep the same priorities:

- White keys as the primary neutral reference.
- Black piano finish not crushed.
- Gold plate believable.
- Skin natural when visible.
- Window highlights controlled.

For this project, keep automated color conservative. The repo can prepare
contact sheets and operator notes, but the actual piano/skin/window judgement
should remain a human or visual-agent decision inside Premiere until there is a
repeatable preset strategy.

## 7. Export

Export YouTube SDR Rec.709:

```text
Format: MP4
Codec: H.264 or H.265
Frame rate: 29.97
Color: Rec.709 SDR
Audio: external audio only
```
