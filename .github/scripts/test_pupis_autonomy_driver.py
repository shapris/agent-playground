#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DRIVER = REPO_ROOT / ".github" / "scripts" / "pupis_autonomy_driver.py"


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def base_state():
    return {
        "scope": "scratch-only",
        "branch": "chat-mode-ci-probe-20260922",
        "canonical_projects_locked": ["PUPIS_EVO", "JARVIS_FRESH"],
        "evidence": {
            "exact_bytes": {
                "sha256": "unused-for-counter-test",
            }
        },
    }


def run_driver(queue, *, optimized=False):
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    write_json(root / "autonomy_queue.json", queue)
    write_json(root / "autonomy_state.json", base_state())

    cmd = [sys.executable]
    if optimized:
        cmd.append("-O")
    cmd.extend([str(DRIVER), "--worktree", str(root)])

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False,
    )
    return temp, root, result


class DriverSafetyTests(unittest.TestCase):
    def test_hard_cap_survives_python_optimized_mode(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 0,
            "max_cycles": 999,
            "tasks": [
                {"id": "x", "kind": "counter", "expected_probe": "CI_PASS"}
            ],
        }
        temp, root, result = run_driver(queue, optimized=True)
        self.addCleanup(temp.cleanup)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("max_cycles outside hard bounds", result.stderr + result.stdout)
        self.assertFalse((root / "driver_probe.txt").exists())

    def test_duplicate_task_ids_are_rejected(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 0,
            "max_cycles": 2,
            "tasks": [
                {"id": "same", "kind": "counter", "expected_probe": "CI_PASS"},
                {"id": "same", "kind": "counter", "expected_probe": "CI_PASS"},
            ],
        }
        temp, root, result = run_driver(queue)
        self.addCleanup(temp.cleanup)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("task ids must be unique", result.stderr + result.stdout)
        self.assertFalse((root / "driver_probe.txt").exists())

    def test_unknown_task_kind_is_rejected(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 0,
            "max_cycles": 1,
            "tasks": [
                {"id": "x", "kind": "arbitrary-code", "expected_probe": "CI_PASS"}
            ],
        }
        temp, root, result = run_driver(queue)
        self.addCleanup(temp.cleanup)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported task kind", result.stderr + result.stdout)
        self.assertFalse((root / "driver_probe.txt").exists())

    def test_legal_counter_task_completes_once(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 0,
            "max_cycles": 1,
            "tasks": [
                {"id": "one", "kind": "counter", "expected_probe": "CI_PASS"}
            ],
            "evidence": [],
        }
        temp, root, result = run_driver(queue)
        self.addCleanup(temp.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        final_queue = json.loads(
            (root / "autonomy_queue.json").read_text(encoding="utf-8")
        )
        self.assertEqual(final_queue["status"], "complete")
        self.assertEqual(final_queue["index"], 1)
        self.assertEqual(final_queue["last_completed"], "one")
        self.assertEqual(
            (root / "driver_probe.txt").read_text(encoding="utf-8"),
            "AUTONOMY_DRIVER_CYCLE=1\nTASK=one\n",
        )


if __name__ == "__main__":
    unittest.main()
