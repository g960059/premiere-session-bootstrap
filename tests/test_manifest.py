from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import yaml

from premiere_session_bootstrap.cli import build_premiere_manifest, ensure_grouped, run_premiere_import, write_premiere_outputs


class ManifestTests(unittest.TestCase):
    def test_build_manifest_marks_external_audio_as_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            take_dir = root / "takes" / "take-01"
            take_dir.mkdir(parents=True)
            (take_dir / "angle-a.mp4").write_bytes(b"")
            (take_dir / "angle-b.mp4").write_bytes(b"")
            (take_dir / "audio.aif").write_bytes(b"")
            session = {
                "session_id": "session-test",
                "session_title": "session-test",
                "session_root": str(root),
                "timeline": {"frame_rate": "29.97"},
                "takes": [{"id": "take-01", "take": "takes/take-01/take.yaml"}],
            }
            take = {
                "source_dir": str(take_dir),
                "master_audio": "audio.aif",
                "camera_files": [
                    {"label": "angle-a", "file": "angle-a.mp4"},
                    {"label": "angle-b", "file": "angle-b.mp4"},
                ],
            }
            (root / "session.yaml").write_text(yaml.safe_dump(session), encoding="utf-8")
            (take_dir / "take.yaml").write_text(yaml.safe_dump(take), encoding="utf-8")

            manifest = build_premiere_manifest(root)

            self.assertEqual(manifest["status"], "PASS")
            self.assertEqual(manifest["premiere_project_name"], "session-test.prproj")
            self.assertEqual(Path(manifest["premiere_project_path"]).name, "session-test.prproj")
            self.assertEqual(manifest["takes"][0]["multicam_name"], "MC_take-01")
            self.assertTrue(manifest["takes"][0]["edit_audio"]["intended_final_audio"])
            self.assertEqual(manifest["takes"][0]["edit_audio"]["file"], "audio.aif")
            self.assertEqual(len(manifest["takes"][0]["camera_files"]), 2)

    def test_write_outputs_generates_import_script_with_manifest_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            take_dir = root / "takes" / "take-01"
            take_dir.mkdir(parents=True)
            (take_dir / "angle-a.mp4").write_bytes(b"")
            (take_dir / "audio.aif").write_bytes(b"")
            session = {
                "session_id": "session-test",
                "session_title": "session-test",
                "timeline": {"frame_rate": "29.97"},
                "takes": [{"id": "take-01", "take": "takes/take-01/take.yaml"}],
            }
            take = {
                "source_dir": str(take_dir),
                "master_audio": "audio.aif",
                "camera_files": [{"label": "angle-a", "file": "angle-a.mp4"}],
            }
            (root / "session.yaml").write_text(yaml.safe_dump(session), encoding="utf-8")
            (take_dir / "take.yaml").write_text(yaml.safe_dump(take), encoding="utf-8")

            payload = write_premiere_outputs(root, project_path=root / "premiere" / "custom.prproj")

            manifest_path = Path(payload["manifest_path"])
            import_jsx_path = Path(payload["import_jsx_path"])
            runbook_path = Path(payload["runbook_path"])
            self.assertTrue(manifest_path.exists())
            self.assertTrue(import_jsx_path.exists())
            self.assertTrue(runbook_path.exists())
            self.assertIn(str(manifest_path), import_jsx_path.read_text(encoding="utf-8"))
            self.assertEqual(Path(payload["premiere_project_path"]).name, "custom.prproj")
            self.assertIn('status: "PASS"', import_jsx_path.read_text(encoding="utf-8"))

    def test_ensure_grouped_accepts_already_grouped_session_without_incoming(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            take_dir = root / "takes" / "take-01"
            take_dir.mkdir(parents=True)
            (take_dir / "angle-a.mp4").write_bytes(b"")
            (take_dir / "audio.aif").write_bytes(b"")
            session = {
                "session_id": "session-test",
                "session_title": "session-test",
                "date": "2026-05-18",
                "session_root": str(root),
                "takes": [{"id": "take-01", "take": "takes/take-01/take.yaml"}],
            }
            take = {
                "session": "session-test",
                "date": "2026-05-18",
                "source_dir": str(take_dir),
                "master_audio": "audio.aif",
                "camera_files": [{"label": "angle-a", "file": "angle-a.mp4"}],
            }
            (root / "session.yaml").write_text(yaml.safe_dump(session), encoding="utf-8")
            (take_dir / "take.yaml").write_text(yaml.safe_dump(take), encoding="utf-8")

            payload, status_code = ensure_grouped(root)

            self.assertEqual(status_code, 0)
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["take_count"], 1)

    def test_run_premiere_import_accepts_fresh_result_from_app_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            jsx = reports / "premiere-bootstrap-import.jsx"
            jsx.write_text("// fake import script\n", encoding="utf-8")
            fake_app = root / "fake-premiere"
            fake_app.write_text(
                "#!/usr/bin/env bash\n"
                "script=\"$3\"\n"
                "reports=\"$(dirname \"$script\")\"\n"
                "cat > \"$reports/premiere-import-result.json\" <<'JSON'\n"
                "{\"status\":\"PASS\",\"take_count\":1}\n"
                "JSON\n",
                encoding="utf-8",
            )
            fake_app.chmod(0o755)

            result = run_premiere_import(root, app_path=fake_app, timeout_seconds=5)

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["take_count"], 1)
            self.assertEqual(result["runner"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
