from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import yaml

from premiere_session_bootstrap.cli import build_premiere_manifest, write_premiere_outputs


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


if __name__ == "__main__":
    unittest.main()
