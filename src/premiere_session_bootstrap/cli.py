from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time
from typing import Any

import yaml

from premiere_session_bootstrap.autogroup import (
    apply_auto_group,
    auto_group_plan_to_dict,
    plan_auto_group,
    write_auto_group_plan_reports,
)
from premiere_session_bootstrap.config import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS, initialize_session


SCHEMA = "premiere-session-bootstrap.manifest.v2"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    status = payload.get("status", "PASS")
    summary = payload.get("summary", "")
    print(f"{status}: {summary}".rstrip())


def _find_incoming_dir(session_root: Path, incoming_dir: str | None) -> Path | None:
    if incoming_dir:
        path = (session_root / incoming_dir).resolve()
        return path if path.is_dir() else None
    path = (session_root / "incoming").resolve()
    return path if path.is_dir() else None


def _incoming_media_count(session_root: Path, incoming_dir: str | None) -> int:
    incoming = _find_incoming_dir(session_root, incoming_dir)
    if incoming is None:
        return 0
    media_extensions = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS
    return sum(
        1
        for path in incoming.iterdir()
        if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in media_extensions
    )


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


def _default_project_path(session_root: Path, session: dict[str, Any]) -> Path:
    project_name = f"{session.get('session_id') or session_root.name}.prproj"
    return session_root / project_name


def build_premiere_manifest(session_root: Path, project_path: Path | None = None) -> dict[str, Any]:
    session_path = session_root / "session.yaml"
    session = _load_yaml(session_path)
    takes = _session_take_rows(session_root, session)
    resolved_project_path = (project_path or _default_project_path(session_root, session)).resolve()
    return {
        "schema": SCHEMA,
        "status": "PASS",
        "session_root": str(session_root.resolve()),
        "session_id": session.get("session_id"),
        "session_title": session.get("session_title"),
        "premiere_project_name": resolved_project_path.name,
        "premiere_project_path": str(resolved_project_path),
        "target_delivery": {
            "platform": "YouTube",
            "dynamic_range": "SDR",
            "color_space": "Rec.709",
            "frame_rate": session.get("timeline", {}).get("frame_rate", "29.97"),
        },
        "automation_expectations": {
            "bin_creation": "expected_scriptable",
            "media_import": "expected_scriptable",
            "multicam_audio_sync": "manual_premiere_ui",
            "external_audio_only": "manual_post_sync_cleanup",
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
        f"- Project path: `{payload['premiere_project_path']}`",
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
            "- The generated Premiere import script creates/opens the project, creates take bins, and imports grouped media.",
            "- This handoff intentionally treats multicam creation as manual; Premiere's public UXP 26.2 API does not expose audio-synced multicam creation.",
            "- The desired audio policy is external AIF/WAV only; camera audio is sync scratch.",
            "- Color can be done with Lumetri presets, Paste Attributes, or adjustment layers depending on the edit.",
            "",
        ]
    )
    return "\n".join(lines)


def _jsx_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_import_jsx(manifest_path: Path) -> str:
    manifest_literal = _jsx_string(str(manifest_path.resolve()))
    return f"""/*
Generated by premiere-session-bootstrap.

Run from a Premiere CEP panel or ExtendScript debugging environment. The script
creates/opens the .prproj named in the manifest, creates take bins, imports the
listed angle videos and final audio files, saves the project, and writes an
import report next to the manifest.

It intentionally does not create audio-synced multicam source sequences.
*/

var MANIFEST_PATH = {manifest_literal};

(function () {{
    function readJson(path) {{
        var file = new File(path);
        if (!file.exists) {{
            throw new Error("Manifest not found: " + path);
        }}
        file.encoding = "UTF-8";
        file.open("r");
        var text = file.read();
        file.close();
        return JSON.parse(text);
    }}

    function writeJson(path, payload) {{
        var file = new File(path);
        file.encoding = "UTF-8";
        file.open("w");
        file.write(JSON.stringify(payload, null, 2));
        file.close();
    }}

    function dirname(path) {{
        var index = Math.max(path.lastIndexOf("/"), path.lastIndexOf("\\\\"));
        return index >= 0 ? path.substring(0, index) : "";
    }}

    function findChildBin(parent, name) {{
        for (var i = 0; i < parent.children.numItems; i++) {{
            var item = parent.children[i];
            if (item && item.name === name && item.type === ProjectItemType.BIN) {{
                return item;
            }}
        }}
        return null;
    }}

    function ensureBinPath(root, names) {{
        var current = root;
        for (var i = 0; i < names.length; i++) {{
            var next = findChildBin(current, names[i]);
            if (!next) {{
                next = current.createBin(names[i]);
                if (!next) {{
                    throw new Error("Failed to create bin: " + names.slice(0, i + 1).join("/"));
                }}
            }}
            current = next;
        }}
        return current;
    }}

    function mediaAlreadyInBin(bin, path) {{
        for (var i = 0; i < bin.children.numItems; i++) {{
            var item = bin.children[i];
            if (!item || item.type === ProjectItemType.BIN) {{
                continue;
            }}
            if (item.getMediaPath && item.getMediaPath() === path) {{
                return true;
            }}
        }}
        return false;
    }}

    function ensureProject(projectPath) {{
        if (!projectPath) {{
            return "used_current_project";
        }}
        if (app.project && app.project.path === projectPath) {{
            return "project_already_open";
        }}
        var projectFile = new File(projectPath);
        if (projectFile.exists) {{
            if (!app.openDocument(projectPath, true, true, true, true)) {{
                throw new Error("Failed to open project: " + projectPath);
            }}
            return "opened_existing_project";
        }}
        var projectFolder = new Folder(dirname(projectPath));
        if (!projectFolder.exists) {{
            projectFolder.create();
        }}
        if (!app.newProject(projectPath)) {{
            throw new Error("Failed to create project: " + projectPath);
        }}
        return "created_new_project";
    }}

    function importMissing(paths, bin) {{
        var missing = [];
        for (var i = 0; i < paths.length; i++) {{
            var path = paths[i];
            if (!new File(path).exists) {{
                throw new Error("Media file not found: " + path);
            }}
            if (!mediaAlreadyInBin(bin, path)) {{
                missing.push(path);
            }}
        }}
        if (missing.length) {{
            if (!app.project.importFiles(missing, true, bin, false)) {{
                throw new Error("Premiere importFiles failed for bin: " + bin.name);
            }}
        }}
        return missing.length;
    }}

    var manifest = readJson(MANIFEST_PATH);
    var report = {{
        schema: "premiere-session-bootstrap.import-result.v1",
        status: "PASS",
        manifest_path: MANIFEST_PATH,
        project_path: manifest.premiere_project_path,
        completed_at: null,
        project_action: null,
        take_count: manifest.takes.length,
        imported_file_count: 0,
        skipped_existing_count: 0,
        takes: []
    }};

    report.project_action = ensureProject(manifest.premiere_project_path);
    var root = app.project.rootItem;

    for (var t = 0; t < manifest.takes.length; t++) {{
        var take = manifest.takes[t];
        var bin = ensureBinPath(root, take.bin_path);
        var paths = [];
        for (var c = 0; c < take.camera_files.length; c++) {{
            paths.push(take.camera_files[c].path);
        }}
        paths.push(take.edit_audio.path);
        var imported = importMissing(paths, bin);
        report.imported_file_count += imported;
        report.skipped_existing_count += paths.length - imported;
        report.takes.push({{
            take_id: take.take_id,
            bin_path: take.bin_path.join("/"),
            multicam_name: take.multicam_name,
            file_count: paths.length,
            imported_file_count: imported,
            skipped_existing_count: paths.length - imported,
            final_audio: take.edit_audio.file,
            next_manual_step: "Select the imported take media, then create a multicam source sequence using Audio sync."
        }});
    }}

    app.project.save();
    report.completed_at = new Date().toISOString();
    var reportPath = dirname(MANIFEST_PATH) + "/premiere-import-result.json";
    writeJson(reportPath, report);
    alert("Premiere bootstrap complete. Imported " + report.imported_file_count + " new file(s); skipped " + report.skipped_existing_count + " existing file(s).\\n\\nNext: create one audio-synced multicam source sequence per take.");
}})();
"""


def render_import_runbook(payload: dict[str, Any], jsx_path: Path) -> str:
    lines = [
        "# Premiere Import Runbook",
        "",
        f"- Project: `{payload['premiere_project_path']}`",
        f"- Manifest: `{payload.get('manifest_path', '')}`",
        f"- Import script: `{jsx_path}`",
        "",
        "## Automated Step",
        "",
        "Run the generated ExtendScript from a CEP panel or VSCode ExtendScript debugging session.",
        "The script will create/open the project, create bins, import grouped media, save the project, and write `premiere-import-result.json`.",
        "",
        "## Manual Step After Import",
        "",
        "For each take bin:",
        "",
        "1. Select all angle videos and the final external audio.",
        "2. Create a Multi-Camera Source Sequence.",
        "3. Set Synchronize Point to `Audio`.",
        "4. Use camera audio only for synchronization.",
        "5. After creation, mute/disable camera scratch audio.",
        "6. Keep `audio.aif` or `audio-edit.wav` as the only final audio.",
        "",
    ]
    for take in payload["takes"]:
        lines.append(f"- `{take['take_id']}` -> `{take['multicam_name']}` -> final audio `{take['edit_audio']['file']}`")
    lines.append("")
    return "\n".join(lines)


def write_premiere_outputs(session_root: Path, project_path: Path | None = None) -> dict[str, Any]:
    payload = build_premiere_manifest(session_root, project_path=project_path)
    reports_dir = session_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = reports_dir / "premiere-manifest.json"
    handoff_path = reports_dir / "premiere-handoff.md"
    payload["manifest_path"] = str(manifest_path)
    payload["handoff_path"] = str(handoff_path)
    import_jsx_path = reports_dir / "premiere-bootstrap-import.jsx"
    runbook_path = reports_dir / "premiere-import-runbook.md"
    payload["import_jsx_path"] = str(import_jsx_path)
    payload["runbook_path"] = str(runbook_path)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    handoff_path.write_text(render_handoff(payload), encoding="utf-8")
    import_jsx_path.write_text(render_import_jsx(manifest_path), encoding="utf-8")
    runbook_path.write_text(render_import_runbook(payload, import_jsx_path), encoding="utf-8")
    return payload


def _default_premiere_app_path() -> Path:
    return Path("/Applications/Adobe Premiere Pro 2026/Adobe Premiere Pro 2026.app/Contents/MacOS/Adobe Premiere Pro 2026")


def run_premiere_import(
    session_root: Path,
    *,
    app_path: Path | None = None,
    jsx_path: Path | None = None,
    timeout_seconds: int = 300,
) -> dict[str, Any]:
    session_root = session_root.resolve()
    reports_dir = session_root / "reports"
    script_path = (jsx_path or reports_dir / "premiere-bootstrap-import.jsx").resolve()
    result_path = reports_dir / "premiere-import-result.json"
    stdout_path = reports_dir / "premiere-import-runner.stdout.log"
    stderr_path = reports_dir / "premiere-import-runner.stderr.log"
    resolved_app_path = (app_path or _default_premiere_app_path()).resolve()

    if not script_path.is_file():
        return {
            "status": "FAIL",
            "summary": f"Premiere import JSX not found: {script_path}",
            "script_path": str(script_path),
            "result_path": str(result_path),
        }
    if not resolved_app_path.is_file():
        return {
            "status": "FAIL",
            "summary": f"Premiere executable not found: {resolved_app_path}",
            "app_path": str(resolved_app_path),
            "script_path": str(script_path),
            "result_path": str(result_path),
        }

    start_time = time.time()
    command = [str(resolved_app_path), "--console", "es.processFile", str(script_path)]
    reports_dir.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)

    deadline = start_time + timeout_seconds
    last_error: str | None = None
    while time.time() < deadline:
        if result_path.exists() and result_path.stat().st_mtime >= start_time:
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                last_error = f"result JSON is invalid: {exc}"
            else:
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
                result["runner"] = {
                    "status": "PASS",
                    "command": command,
                    "stdout_log": str(stdout_path),
                    "stderr_log": str(stderr_path),
                    "timeout_seconds": timeout_seconds,
                }
                return result

        return_code = process.poll()
        if return_code is not None and return_code != 0:
            break
        time.sleep(1)

    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    stderr_tail = ""
    if stderr_path.exists():
        stderr_tail = "\n".join(stderr_path.read_text(encoding="utf-8", errors="replace").splitlines()[-20:])
    summary = last_error or "Premiere did not produce premiere-import-result.json before timeout"
    return {
        "status": "FAIL",
        "summary": summary,
        "app_path": str(resolved_app_path),
        "script_path": str(script_path),
        "result_path": str(result_path),
        "command": command,
        "return_code": process.poll(),
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "stderr_tail": stderr_tail,
    }


def command_group_session(args: argparse.Namespace) -> int:
    session_root = Path(args.session_root).resolve()
    payload, status_code = ensure_grouped(session_root, incoming_dir=args.incoming_dir, dry_run=args.dry_run)
    _emit(payload, as_json=args.json)
    return status_code


def ensure_grouped(session_root: Path, *, incoming_dir: str | None = None, dry_run: bool = False) -> tuple[dict[str, Any], int]:
    media_count = _incoming_media_count(session_root, incoming_dir)

    if media_count == 0:
        session = initialize_session(session_root)
        payload = {
            "status": "PASS",
            "summary": f"session already grouped; {len(session.takes)} takes available",
            "session_config": str(session.session_path),
            "take_count": len(session.takes),
        }
        return payload, 0

    plan = plan_auto_group(session_root, incoming_dir=incoming_dir)
    write_auto_group_plan_reports(session_root, plan)

    if dry_run:
        payload = auto_group_plan_to_dict(plan)
        payload["summary"] = f"planned {len(plan.takes)} takes from {plan.incoming_dir}"
        return payload, 0 if plan.status == "PASS" else 1

    if plan.status != "PASS":
        payload = auto_group_plan_to_dict(plan)
        payload["summary"] = "grouping plan is not PASS; refusing to apply"
        return payload, 1

    apply_result = apply_auto_group(session_root, plan=plan)
    session = initialize_session(session_root)
    payload = {
        "status": apply_result.status,
        "summary": f"applied {len(apply_result.takes_created)} takes",
        "session_config": str(session.session_path),
        "takes_created": apply_result.takes_created,
        "excluded_created": apply_result.excluded_created,
    }
    return payload, 0


def command_premiere_manifest(args: argparse.Namespace) -> int:
    session_root = Path(args.session_root).resolve()
    project_path = Path(args.project_path).resolve() if args.project_path else None
    payload = write_premiere_outputs(session_root, project_path=project_path)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"PASS: {payload['summary']}")
        print(f"Manifest: {payload['manifest_path']}")
        print(f"Handoff: {payload['handoff_path']}")
        print(f"Import JSX: {payload['import_jsx_path']}")
        print(f"Runbook: {payload['runbook_path']}")
    return 0


def command_bootstrap_session(args: argparse.Namespace) -> int:
    session_root = Path(args.session_root).resolve()
    group_payload, group_status = ensure_grouped(session_root, incoming_dir=args.incoming_dir)
    if group_status != 0:
        _emit(group_payload, as_json=args.json)
        return group_status
    payload = write_premiere_outputs(
        session_root,
        project_path=Path(args.project_path).resolve() if args.project_path else None,
    )
    payload["grouping"] = group_payload
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"PASS: {payload['summary']}")
        print(f"Manifest: {payload['manifest_path']}")
        print(f"Import JSX: {payload['import_jsx_path']}")
        print(f"Runbook: {payload['runbook_path']}")
    return 0


def command_run_premiere_import(args: argparse.Namespace) -> int:
    session_root = Path(args.session_root).resolve()
    if not (session_root / "reports" / "premiere-bootstrap-import.jsx").is_file():
        write_premiere_outputs(
            session_root,
            project_path=Path(args.project_path).resolve() if args.project_path else None,
        )
    payload = run_premiere_import(
        session_root,
        app_path=Path(args.app_path).resolve() if args.app_path else None,
        jsx_path=Path(args.jsx_path).resolve() if args.jsx_path else None,
        timeout_seconds=args.timeout,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{payload.get('status', 'FAIL')}: {payload.get('summary', 'Premiere import runner finished')}")
        if payload.get("result_path"):
            print(f"Result: {payload['result_path']}")
        if payload.get("stderr_log"):
            print(f"stderr log: {payload['stderr_log']}")
    return 0 if payload.get("status") == "PASS" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="premiere-session-bootstrap")
    subparsers = parser.add_subparsers(dest="command", required=True)

    group = subparsers.add_parser("group-session", help="group incoming media into takes")
    group.add_argument("session_root")
    group.add_argument("--incoming-dir")
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--json", action="store_true")
    group.set_defaults(func=command_group_session)

    manifest = subparsers.add_parser("premiere-manifest", help="write Premiere manifest and handoff")
    manifest.add_argument("session_root")
    manifest.add_argument("--project-path", help="Premiere .prproj path to create/open from the generated import script")
    manifest.add_argument("--json", action="store_true")
    manifest.set_defaults(func=command_premiere_manifest)

    bootstrap = subparsers.add_parser("bootstrap-session", help="group incoming media and write Premiere import handoff")
    bootstrap.add_argument("session_root")
    bootstrap.add_argument("--incoming-dir")
    bootstrap.add_argument("--project-path", help="Premiere .prproj path to create/open from the generated import script")
    bootstrap.add_argument("--json", action="store_true")
    bootstrap.set_defaults(func=command_bootstrap_session)

    run_import = subparsers.add_parser("run-premiere-import", help="run generated Premiere import JSX and verify import result")
    run_import.add_argument("session_root")
    run_import.add_argument("--project-path", help="Generate handoff first with this .prproj path if import JSX is missing")
    run_import.add_argument("--jsx-path", help="Path to a specific Premiere import JSX")
    run_import.add_argument("--app-path", help="Path to the Premiere Pro executable")
    run_import.add_argument("--timeout", type=int, default=300)
    run_import.add_argument("--json", action="store_true")
    run_import.set_defaults(func=command_run_premiere_import)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
