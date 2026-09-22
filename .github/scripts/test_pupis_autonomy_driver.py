#!/usr/bin/env python3
import hashlib
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
        "schema": 1,
        "scope": "scratch-only",
        "repository": "shapris/agent-playground",
        "branch": "chat-mode-ci-probe-20260922",
        "pull_request": 1,
        "canonical_projects_locked": ["PUPIS_EVO", "JARVIS_FRESH"],
        "invariants": [],
        "evidence": {
            "exact_bytes": {
                "sha256": "unused-for-counter-test",
            }
        },
    }


def run_driver(queue, *, optimized=False, extra_files=None):
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    write_json(root / "autonomy_queue.json", queue)
    write_json(root / "autonomy_state.json", base_state())
    for name, content in (extra_files or {}).items():
        (root / name).write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))

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

    def test_queue_integrity_recheck_accepts_valid_prefix(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 1,
            "max_cycles": 2,
            "tasks": [
                {"id": "done", "kind": "counter", "expected_probe": "CI_PASS"},
                {"id": "audit", "kind": "queue-integrity-recheck", "expected_probe": "CI_PASS"},
            ],
            "evidence": [
                {"index": 0, "task_id": "done", "kind": "counter", "result": "PASS"}
            ],
        }
        temp, root, result = run_driver(queue)
        self.addCleanup(temp.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        final_queue = json.loads((root / "autonomy_queue.json").read_text(encoding="utf-8"))
        self.assertEqual(final_queue["last_completed"], "audit")
        self.assertEqual(final_queue["evidence"][-1]["details"]["verified_records"], 1)

    def test_queue_integrity_recheck_rejects_mismatched_evidence(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 1,
            "max_cycles": 2,
            "tasks": [
                {"id": "done", "kind": "counter", "expected_probe": "CI_PASS"},
                {"id": "audit", "kind": "queue-integrity-recheck", "expected_probe": "CI_PASS"},
            ],
            "evidence": [
                {"index": 0, "task_id": "WRONG", "kind": "counter", "result": "PASS"}
            ],
        }
        temp, root, result = run_driver(queue)
        self.addCleanup(temp.cleanup)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("queue evidence task mismatch", result.stderr + result.stdout)

    def test_critical_hash_snapshot_records_all_critical_files(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 0,
            "max_cycles": 1,
            "tasks": [
                {"id": "hash", "kind": "critical-hash-snapshot", "expected_probe": "CI_PASS"}
            ],
            "evidence": [],
        }
        extra = {
            "chat_mode_ci_probe.py": "print('ok')\n",
            "exact_bytes_probe.py": b"\xef\xbb\xbfVALUE=1\r\n",
            "race_guard_probe.txt": "VERSION=3_RECOVERED\n",
        }
        temp, root, result = run_driver(queue, extra_files=extra)
        self.addCleanup(temp.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        final_queue = json.loads((root / "autonomy_queue.json").read_text(encoding="utf-8"))
        hashes = final_queue["evidence"][-1]["details"]["sha256"]
        self.assertEqual(set(hashes), {
            "chat_mode_ci_probe.py",
            "exact_bytes_probe.py",
            "race_guard_probe.txt",
            "autonomy_queue.json",
        })
        self.assertEqual(
            hashes["chat_mode_ci_probe.py"],
            hashlib.sha256(extra["chat_mode_ci_probe.py"].encode("utf-8")).hexdigest(),
        )

    def test_symlink_guard_rejects_critical_symlink(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 0,
            "max_cycles": 1,
            "tasks": [
                {"id": "links", "kind": "symlink-guard", "expected_probe": "CI_PASS"}
            ],
            "evidence": [],
        }
        temp, root, result = run_driver(queue)
        self.addCleanup(temp.cleanup)
        # Re-run manually after creating the critical files/symlink.
        (root / "chat_mode_ci_probe.py").write_text("print('ok')\n", encoding="utf-8")
        (root / "exact_bytes_probe.py").write_text("x=1\n", encoding="utf-8")
        (root / "race_guard_probe.txt").write_text("VERSION=3_RECOVERED\n", encoding="utf-8")
        target = root / "real_state.json"
        write_json(target, base_state())
        (root / "autonomy_state.json").unlink()
        (root / "autonomy_state.json").symlink_to(target)
        write_json(root / "autonomy_queue.json", queue)
        cmd = [sys.executable, str(DRIVER), "--worktree", str(root)]
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("critical symlinks are forbidden", result.stderr + result.stdout)

    def test_probe_syntax_recheck_rejects_invalid_python(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 0,
            "max_cycles": 1,
            "tasks": [
                {"id": "syntax", "kind": "probe-syntax-recheck", "expected_probe": "CI_PASS"}
            ],
            "evidence": [],
        }
        temp, root, result = run_driver(
            queue,
            extra_files={"chat_mode_ci_probe.py": "def broken(:\n"},
        )
        self.addCleanup(temp.cleanup)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SyntaxError", result.stderr + result.stdout)



    def test_state_schema_recheck_rejects_wrong_schema(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 0,
            "max_cycles": 1,
            "tasks": [
                {"id": "schema", "kind": "state-schema-recheck", "expected_probe": "CI_PASS"}
            ],
            "evidence": [],
            "safety": [],
        }
        temp, root, result = run_driver(queue)
        self.addCleanup(temp.cleanup)
        state = base_state()
        state["schema"] = 999
        write_json(root / "autonomy_state.json", state)
        result = subprocess.run(
            [sys.executable, str(DRIVER), "--worktree", str(root)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("state schema must be 1", result.stderr + result.stdout)

    def test_critical_size_bounds_rejects_empty_file(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 0,
            "max_cycles": 1,
            "tasks": [
                {"id": "sizes", "kind": "critical-size-bounds", "expected_probe": "CI_PASS"}
            ],
            "evidence": [],
            "safety": [],
        }
        extra = {
            "chat_mode_ci_probe.py": b"",
            "exact_bytes_probe.py": b"\xef\xbb\xbfX\r\n",
            "race_guard_probe.txt": "VERSION=3_RECOVERED\n",
        }
        temp, root, result = run_driver(queue, extra_files=extra)
        self.addCleanup(temp.cleanup)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("critical file size out of bounds", result.stderr + result.stdout)

    def test_encoding_profile_recheck_accepts_expected_profiles(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 0,
            "max_cycles": 1,
            "tasks": [
                {"id": "encoding", "kind": "encoding-profile-recheck", "expected_probe": "CI_PASS"}
            ],
            "evidence": [],
            "safety": [],
        }
        extra = {
            "chat_mode_ci_probe.py": b'print("OK")\n',
            "exact_bytes_probe.py": b"\xef\xbb\xbfVALUE=1\r\nTAIL=2\r\n",
            "race_guard_probe.txt": "VERSION=3_RECOVERED\n",
        }
        temp, root, result = run_driver(queue, extra_files=extra)
        self.addCleanup(temp.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_probe_capability_recheck_rejects_import(self):
        queue = {
            "schema": 1,
            "scope": "scratch-only",
            "branch": "chat-mode-ci-probe-20260922",
            "status": "active",
            "index": 0,
            "max_cycles": 1,
            "tasks": [
                {"id": "cap", "kind": "probe-capability-recheck", "expected_probe": "CI_PASS"}
            ],
            "evidence": [],
            "safety": [],
        }
        extra = {
            "chat_mode_ci_probe.py": "import os\nprint('OK')\n",
            "exact_bytes_probe.py": b"\xef\xbb\xbfX\r\n",
            "race_guard_probe.txt": "VERSION=3_RECOVERED\n",
        }
        temp, root, result = run_driver(queue, extra_files=extra)
        self.addCleanup(temp.cleanup)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("permits only expression statements", result.stderr + result.stdout)

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
