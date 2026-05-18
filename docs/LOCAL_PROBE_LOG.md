# Local Probe Log

Date: 2026-05-18

## Host

- App: Adobe Premiere Pro 2026
- Version observed in UXP log: 26.2.2
- Platform: macOS / Apple Silicon

## Results

- Premiere launches and responds to basic AppleScript activation/name checks.
- Command-line ExtendScript execution with `/C es.processFile` is not usable on
  this machine. It spawned a second Premiere process and crashed/hung before
  writing probe output.
- User-level CEP extension installation completed, but Premiere 2026 did not
  log or auto-load the probe after restart.
- System-level Adobe extension directories are not writable by the current
  shell without administrator elevation.
- `@adobe/premierepro@26.2.0` was inspected from npm. Public UXP APIs include
  project creation/opening, media import, ordinary sequence creation, and
  sequence editing actions. No public API for audio-synced multicam source
  sequence creation was found in the type definitions.
- A Premiere handoff manifest was generated successfully for
  `/Volumes/PortableSSD/phase2-e2e-skill-fresh-agent-test-20260517-011413`.

## Current Verdict

The repo can safely automate Premiere handoff preparation: grouped metadata,
take-level manifests, bin/import instructions, and operator checklists.

The core Premiere operation the user cares about most, one sound-synced multicam
source sequence per take with only external AIF/WAV as final audio, remains a
manual UI step unless an ExtendScript/QE probe later exposes a stable private
route.
