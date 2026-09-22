#!/usr/bin/env python3
import argparse
import ast
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
    "queue-integrity-recheck",
    "critical-hash-snapshot",
    "symlink-guard",
    "probe-syntax-recheck",
    "state-schema-recheck",
    "critical-size-bounds",
    "encoding-profile-recheck",
    "probe-capability-recheck",
}


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True)
    args = parser.parse_args()

    root = Path(args.worktree).resolve()
    queue_path = root / "autonomy_queue.json"
    state_path = root / "autonomy_state.json"

    queue = load_json(queue_path)
    state = load_json(state_path)

    require(queue.get("schema") == 1, "queue schema must be 1")
    require(queue.get("scope") == "scratch-only", "queue scope must be scratch-only")
    require(queue.get("branch") == SCRATCH_BRANCH, "queue branch mismatch")
    require(state.get("scope") == "scratch-only", "state scope must be scratch-only")
    require(state.get("branch") == SCRATCH_BRANCH, "state branch mismatch")
    require(
        set(state.get("canonical_projects_locked", [])) == CANONICAL_LOCKS,
        "canonical project locks mismatch",
    )

    queue_status = queue.get("status")
    require(queue_status in {"active", "complete"}, f"invalid queue status: {queue_status!r}")
    if queue_status != "active":
        print(f"DRIVER_NOOP status={queue_status}")
        return

    try:
        index = int(queue.get("index", 0))
        max_cycles = int(queue["max_cycles"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError("queue index/max_cycles must be valid integers") from exc

    tasks = queue.get("tasks")
    require(isinstance(tasks, list), "queue tasks must be a list")
    require(1 <= max_cycles <= HARD_MAX_CYCLES, f"max_cycles outside hard bounds: {max_cycles}")
    require(1 <= len(tasks) <= HARD_MAX_CYCLES, f"task count outside hard bounds: {len(tasks)}")
    require(0 <= index <= max_cycles, f"queue index outside bounds: {index}")
    require(index <= len(tasks), f"queue index exceeds task count: {index}>{len(tasks)}")

    task_ids = []
    for task in tasks:
        require(isinstance(task, dict), "every queue task must be an object")
        task_id = task.get("id")
        kind = task.get("kind")
        require(isinstance(task_id, str) and bool(task_id), "task id must be a non-empty string")
        require(kind in ALLOWED_TASK_KINDS, f"unsupported task kind: {kind!r}")
        require(task.get("expected_probe") == "CI_PASS", f"task {task_id} lacks CI_PASS gate")
        task_ids.append(task_id)

    require(len(task_ids) == len(set(task_ids)), "task ids must be unique")

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
        require(actual == expected, f"exact-byte SHA mismatch: {actual} != {expected}")
        details["sha256"] = actual

    elif kind == "race-guard-recheck":
        actual = (root / "race_guard_probe.txt").read_text(encoding="utf-8")
        require(actual == "VERSION=3_RECOVERED\n", f"race guard mismatch: {actual!r}")
        details["race_guard"] = actual.strip()

    elif kind == "continuity-seal":
        probe = (root / "chat_mode_ci_probe.py").read_text(encoding="utf-8")
        require("DRIVE_TO_GITHUB_CI_OK" in probe, "continuity marker missing")
        require("SystemExit" not in probe, "unsafe SystemExit remains in probe")
        details["probe_safe"] = True

    elif kind == "queue-integrity-recheck":
        evidence = queue.get("evidence", [])
        require(isinstance(evidence, list), "queue evidence must be a list")
        require(len(evidence) == index, f"queue evidence length mismatch: {len(evidence)} != {index}")
        seen = []
        for position, record in enumerate(evidence):
            require(isinstance(record, dict), "queue evidence record must be an object")
            require(record.get("index") == position, f"queue evidence index mismatch at {position}")
            require(record.get("task_id") == tasks[position].get("id"), f"queue evidence task mismatch at {position}")
            require(record.get("result") == "PASS", f"queue evidence result mismatch at {position}")
            seen.append(record.get("task_id"))
        require(len(seen) == len(set(seen)), "queue evidence task ids must be unique")
        details["verified_records"] = len(evidence)

    elif kind == "critical-hash-snapshot":
        critical = [
            "chat_mode_ci_probe.py",
            "exact_bytes_probe.py",
            "race_guard_probe.txt",
            "autonomy_queue.json",
        ]
        hashes = {}
        for name in critical:
            path = root / name
            require(path.exists(), f"critical file missing: {name}")
            require(path.is_file(), f"critical path is not a file: {name}")
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        details["sha256"] = hashes

    elif kind == "symlink-guard":
        critical = [
            "chat_mode_ci_probe.py",
            "exact_bytes_probe.py",
            "race_guard_probe.txt",
            "autonomy_queue.json",
            "autonomy_state.json",
        ]
        bad = [name for name in critical if (root / name).is_symlink()]
        require(not bad, f"critical symlinks are forbidden: {bad}")
        details["checked"] = critical

    elif kind == "probe-syntax-recheck":
        probe_path = root / "chat_mode_ci_probe.py"
        source = probe_path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(probe_path))
        details["syntax"] = "PASS"

    elif kind == "state-schema-recheck":
        require(state.get("schema") == 1, "state schema must be 1")
        require(state.get("repository") == "shapris/agent-playground", "state repository mismatch")
        require(state.get("pull_request") == 1, "state pull_request must be 1")
        require(isinstance(state.get("evidence"), dict), "state evidence must be an object")
        require(isinstance(state.get("invariants"), list), "state invariants must be a list")
        require(isinstance(queue.get("evidence", []), list), "queue evidence must be a list")
        require(isinstance(queue.get("safety", []), list), "queue safety must be a list")
        details["schema"] = "PASS"

    elif kind == "critical-size-bounds":
        critical = [
            "chat_mode_ci_probe.py",
            "exact_bytes_probe.py",
            "race_guard_probe.txt",
            "autonomy_queue.json",
            "autonomy_state.json",
        ]
        sizes = {}
        for name in critical:
            path = root / name
            require(path.exists() and path.is_file(), f"critical file invalid: {name}")
            size = path.stat().st_size
            require(0 < size <= 1024 * 1024, f"critical file size out of bounds: {name}={size}")
            sizes[name] = size
        details["bytes"] = sizes

    elif kind == "encoding-profile-recheck":
        exact = (root / "exact_bytes_probe.py").read_bytes()
        probe = (root / "chat_mode_ci_probe.py").read_bytes()

        require(exact.startswith(b"\xef\xbb\xbf"), "exact-bytes probe must keep UTF-8 BOM")
        exact_text = exact[3:].decode("utf-8")
        require("\r\n" in exact_text, "exact-bytes probe must contain CRLF")
        require("\n" not in exact_text.replace("\r\n", ""), "exact-bytes probe has bare LF")

        require(not probe.startswith(b"\xef\xbb\xbf"), "chat probe must not contain UTF-8 BOM")
        probe.decode("utf-8")
        require(b"\r\n" not in probe, "chat probe must be LF-only")
        require(b"\n" in probe, "chat probe must contain LF")
        details["profile"] = "BOM+CRLF exact / UTF8+LF probe"

    elif kind == "probe-capability-recheck":
        probe_path = root / "chat_mode_ci_probe.py"
        tree = ast.parse(probe_path.read_text(encoding="utf-8"), filename=str(probe_path))
        require(bool(tree.body), "chat probe must not be empty")
        for stmt in tree.body:
            require(isinstance(stmt, ast.Expr), "chat probe permits only expression statements")
            call = stmt.value
            require(isinstance(call, ast.Call), "chat probe permits only calls")
            require(isinstance(call.func, ast.Name) and call.func.id == "print", "chat probe permits only print")
            require(not call.keywords, "chat probe print keywords are forbidden")
            require(len(call.args) == 1, "chat probe print must have exactly one argument")
            require(isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str),
                    "chat probe print argument must be a constant string")
        details["capability"] = "PRINT_CONSTANTS_ONLY"

    else:
        raise ValidationError(f"unsupported bounded task kind: {kind}")

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
        "hard_max_cycles": HARD_MAX_CYCLES,
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
