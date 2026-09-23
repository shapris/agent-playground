import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workspace"))
from task_graph import TaskGraph


class TaskGraphTests(unittest.TestCase):
    def test_ready_tasks_are_lexicographically_sorted(self):
        graph = TaskGraph({
            "compile": {"fetch"},
            "lint": set(),
            "fetch": set(),
            "package": {"compile", "lint"},
        })
        self.assertEqual(graph.ready_tasks(), ["fetch", "lint"])
        self.assertEqual(graph.ready_tasks({"fetch"}), ["compile", "lint"])
        self.assertEqual(graph.ready_tasks({"fetch", "lint", "compile"}), ["package"])

    def test_unknown_completed_names_do_not_change_semantics(self):
        graph = TaskGraph({"a": set(), "b": {"a"}})
        self.assertEqual(graph.ready_tasks({"ghost"}), ["a"])

    def test_cycle_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            TaskGraph({"a": {"b"}, "b": {"a"}})

    def test_non_string_task_identifier_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "task identifiers"):
            TaskGraph({1: set(), "1": {"x"}})

    def test_non_string_dependency_identifier_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "dependency identifiers"):
            TaskGraph({"a": {1}})

    def test_string_dependency_collection_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-string collection"):
            TaskGraph({"compile": "fetch"})

    def test_scalar_string_completed_collection_is_rejected(self):
        graph = TaskGraph({"fetch": set(), "compile": {"fetch"}})
        with self.assertRaisesRegex(ValueError, "non-string collection"):
            graph.ready_tasks("fetch")

    def test_bytes_completed_collection_is_rejected(self):
        graph = TaskGraph({"a": set()})
        with self.assertRaisesRegex(ValueError, "non-string collection"):
            graph.ready_tasks(b"a")


if __name__ == "__main__":
    unittest.main()
