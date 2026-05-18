from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import yaml

from premiere_session_bootstrap.cli import build_premiere_manifest


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
            self.assertEqual(manifest["takes"][0]["multicam_name"], "MC_take-01")
            self.assertTrue(manifest["takes"][0]["edit_audio"]["intended_final_audio"])
            self.assertEqual(manifest["takes"][0]["edit_audio"]["file"], "audio.aif")
            self.assertEqual(len(manifest["takes"][0]["camera_files"]), 2)


if __name__ == "__main__":
    unittest.main()
