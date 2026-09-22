#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


SCRATCH_BRANCH = "chat-mode-ci-probe-20260922"
CANONICAL_LOCKS = {"PUPIS_EVO", "JARVIS_FRESH"}
HARD_MAX_CYCLES = 6
ALLOWED_TASK_KINDS = {
    "counter",
    "exact-byte-recheck",
    "race-guard-recheck",
    "continuity-seal",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True)
    args = parser.parse_args()

    root = Path(args.worktree).resolve()
    queue_path = root / "autonomy_queue.json"
    state_path = root / "autonomy_state.json"

    queue = load_json(queue_path)
    state = load_json(state_path)

    assert queue["schema"] == 1
    assert queue["scope"] == "scratch-only"
    assert queue["branch"] == SCRATCH_BRANCH
    assert state["scope"] == "scratch-only"
    assert state["branch"] == SCRATCH_BRANCH
    assert set(state["canonical_projects_locked"]) == CANONICAL_LOCKS

    if queue.get("status") != "active":
        print(f"DRIVER_NOOP status={queue.get('status')}")
        return

    index = int(queue.get("index", 0))
    tasks = queue["tasks"]
    max_cycles = int(queue["max_cycles"])

    assert 1 <= max_cycles <= HARD_MAX_CYCLES, max_cycles
    assert 1 <= len(tasks) <= HARD_MAX_CYCLES, len(tasks)
    assert 0 <= index <= max_cycles, index
    task_ids = [task["id"] for task in tasks]
    assert len(task_ids) == len(set(task_ids)), task_ids
    for task in tasks:
        assert task["kind"] in ALLOWED_TASK_KINDS, task["kind"]
        assert task.get("expected_probe") == "CI_PASS", task

    if index >= len(tasks) or index >= max_cycles:
        queue["status"] = "complete"
        write_json(queue_path, queue)
        print("DRIVER_SEALED_COMPLETE")
        return

    task = tasks[index]
    task_id = task["id"]
    kind = task["kind"]
    details = {}

    if kind == "counter":
        (root / "driver_probe.txt").write_text(
            f"AUTONOMY_DRIVER_CYCLE={index + 1}\nTASK={task_id}\n",
            encoding="utf-8",
        )
        details["driver_probe"] = f"cycle-{index + 1}"

    elif kind == "exact-byte-recheck":
        expected = state["evidence"]["exact_bytes"]["sha256"]
        actual = hashlib.sha256((root / "exact_bytes_probe.py").read_bytes()).hexdigest()
        assert actual == expected, (actual, expected)
        details["sha256"] = actual

    elif kind == "race-guard-recheck":
        actual = (root / "race_guard_probe.txt").read_text(encoding="utf-8")
        assert actual == "VERSION=3_RECOVERED\n"
        details["race_guard"] = actual.strip()

    elif kind == "continuity-seal":
        probe = (root / "chat_mode_ci_probe.py").read_text(encoding="utf-8")
        assert 'DRIVE_TO_GITHUB_CI_OK' in probe
        assert 'SystemExit' not in probe
        details["probe_safe"] = True

    else:
        raise RuntimeError(f"Unsupported bounded task kind: {kind}")

    now = datetime.now(timezone.utc).isoformat()
    record = {
        "index": index,
        "task_id": task_id,
        "kind": kind,
        "result": "PASS",
        "verified_at_utc": now,
        "details": details,
    }
    queue.setdefault("evidence", []).append(record)
    queue["last_completed"] = task_id
    queue["index"] = index + 1
    if queue["index"] >= len(tasks) or queue["index"] >= max_cycles:
        queue["status"] = "complete"

    state.setdefault("evidence", {})["bounded_autonomy_driver"] = {
        "status": "COMPLETE" if queue["status"] == "complete" else "RUNNING",
        "completed_cycles": queue["index"],
        "max_cycles": max_cycles,
        "last_task": task_id,
        "last_verified_utc": now,
    }

    write_json(queue_path, queue)
    write_json(state_path, state)
    print(
        f"DRIVER_ADVANCED task={task_id} index={queue['index']} "
        f"status={queue['status']}"
    )


if __name__ == "__main__":
    main()
