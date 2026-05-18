from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _session_take_rows(session_root: Path, session: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for take_ref in session.get("takes") or []:
        take_id = take_ref["id"]
        take_path = session_root / take_ref["take"]
        take = _load_yaml(take_path)
        take_dir = Path(take.get("source_dir") or take_path.parent)
        if not take_dir.is_absolute():
            take_dir = (session_root / take_dir).resolve()
        camera_files = []
        for camera in take.get("camera_files") or []:
            file_path = take_dir / camera["file"]
            camera_files.append(
                {
                    "label": camera["label"],
                    "file": camera["file"],
                    "path": str(file_path.resolve()),
                }
            )
        master_audio = take["master_audio"]
        edit_audio = take.get("edit_audio") or master_audio
        rows.append(
            {
                "take_id": take_id,
                "take_path": str(take_path.resolve()),
                "bin_path": ["Piano Session", "Takes", take_id],
                "multicam_name": f"MC_{take_id}",
                "sequence_name": f"SEQ_{take_id}",
                "camera_files": camera_files,
                "master_audio": {
                    "file": master_audio,
                    "path": str((take_dir / master_audio).resolve()),
                },
                "edit_audio": {
                    "file": edit_audio,
                    "path": str((take_dir / edit_audio).resolve()),
                    "intended_final_audio": True,
                },
                "premiere_manual_steps": [
                    "Import all listed media into this take bin.",
                    "Create a multicam source sequence using Audio/Sound synchronization.",
                    "Use camera audio only for sync.",
                    "After sync, mute/disable camera scratch audio.",
                    "Keep the external AIF/WAV edit audio as the final audio source.",
                ],
            }
        )
    return rows


def build_premiere_manifest(session_root: Path) -> dict[str, Any]:
    session_path = session_root / "session.yaml"
    session = _load_yaml(session_path)
    takes = _session_take_rows(session_root, session)
    return {
        "schema": "premiere-session-bootstrap.manifest.v1",
        "status": "PASS",
        "session_root": str(session_root.resolve()),
        "session_id": session.get("session_id"),
        "session_title": session.get("session_title"),
        "premiere_project_name": f"{session.get('session_id') or session_root.name}.prproj",
        "target_delivery": {
            "platform": "YouTube",
            "dynamic_range": "SDR",
            "color_space": "Rec.709",
            "frame_rate": session.get("timeline", {}).get("frame_rate", "29.97"),
        },
        "automation_expectations": {
            "bin_creation": "expected_scriptable",
            "media_import": "expected_scriptable",
            "multicam_audio_sync": "requires_premiere_api_probe",
            "external_audio_only": "requires_premiere_api_probe_or_manual_step",
            "lumetri_color": "preset_or_manual_workflow",
        },
        "takes": takes,
        "summary": f"Premiere manifest generated for {len(takes)} take(s)",
    }


def render_handoff(payload: dict[str, Any]) -> str:
    lines = [
        "# Premiere Operator Handoff",
        "",
        f"- Session: `{payload.get('session_title')}` (`{payload.get('session_id')}`)",
        f"- Session root: `{payload['session_root']}`",
        f"- Suggested project: `{payload['premiere_project_name']}`",
        f"- Take count: {len(payload['takes'])}",
        "",
        "## Automation Status",
        "",
    ]
    for key, value in payload["automation_expectations"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Takes",
            "",
        ]
    )
    for take in payload["takes"]:
        lines.extend(
            [
                f"### {take['take_id']}",
                "",
                f"- Bin path: `{' / '.join(take['bin_path'])}`",
                f"- Multicam source sequence: `{take['multicam_name']}`",
                f"- Final audio: `{take['edit_audio']['file']}`",
                "- Camera angles:",
            ]
        )
        for camera in take["camera_files"]:
            lines.append(f"  - `{camera['label']}`: `{camera['file']}`")
        lines.extend(
            [
                "",
                "Manual Premiere steps:",
                "",
            ]
        )
        for index, step in enumerate(take["premiere_manual_steps"], start=1):
            lines.append(f"{index}. {step}")
        lines.append("")
    lines.extend(
        [
            "## Notes",
            "",
            "- This handoff intentionally treats multicam creation as manual until the Premiere API probe proves it can be automated reliably.",
            "- The desired audio policy is external AIF/WAV only; camera audio is sync scratch.",
            "- Color can be done with Lumetri presets, Paste Attributes, or adjustment layers depending on the edit.",
            "",
        ]
    )
    return "\n".join(lines)


def command_premiere_manifest(args: argparse.Namespace) -> int:
    session_root = Path(args.session_root).resolve()
    payload = build_premiere_manifest(session_root)
    reports_dir = session_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = reports_dir / "premiere-manifest.json"
    handoff_path = reports_dir / "premiere-handoff.md"
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    handoff_path.write_text(render_handoff(payload), encoding="utf-8")
    payload["manifest_path"] = str(manifest_path)
    payload["handoff_path"] = str(handoff_path)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"PASS: {payload['summary']}")
        print(f"Manifest: {manifest_path}")
        print(f"Handoff: {handoff_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="premiere-session-bootstrap")
    subparsers = parser.add_subparsers(dest="command", required=True)
    manifest = subparsers.add_parser("premiere-manifest", help="write Premiere manifest and handoff")
    manifest.add_argument("session_root")
    manifest.add_argument("--json", action="store_true")
    manifest.set_defaults(func=command_premiere_manifest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
