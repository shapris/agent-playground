import unittest

from generative_lab.workspace.failure_memory import FailureMemory


class FailureMemoryTests(unittest.TestCase):
    def test_unseen_strategy_is_allowed(self):
        memory = FailureMemory()
        self.assertTrue(memory.may_attempt("strategy-a", "log-v1"))

    def test_same_fingerprint_and_evidence_is_blocked(self):
        memory = FailureMemory()
        memory.record_failure("strategy-a", "log-v1")
        self.assertFalse(memory.may_attempt("strategy-a", "log-v1"))
        with self.assertRaisesRegex(ValueError, "strategy-a"):
            memory.require_attempt_allowed("strategy-a", "log-v1")

    def test_changed_evidence_allows_reconsideration(self):
        memory = FailureMemory()
        memory.record_failure("strategy-a", "log-v1")
        self.assertTrue(memory.may_attempt("strategy-a", "log-v2"))

    def test_other_fingerprint_is_independent(self):
        memory = FailureMemory()
        memory.record_failure("strategy-a", "log-v1")
        self.assertTrue(memory.may_attempt("strategy-b", "log-v1"))

    def test_all_failed_evidence_values_remain_blocked(self):
        memory = FailureMemory()
        memory.record_failure("strategy-a", "log-v1")
        memory.record_failure("strategy-a", "log-v2")
        self.assertFalse(memory.may_attempt("strategy-a", "log-v1"))
        self.assertFalse(memory.may_attempt("strategy-a", "log-v2"))
        self.assertTrue(memory.may_attempt("strategy-a", "log-v3"))
        self.assertEqual(memory.snapshot()["strategy-a"], ["log-v1", "log-v2"])

    def test_empty_fingerprint_is_rejected_consistently(self):
        memory = FailureMemory()
        for action in (
            lambda: memory.record_failure("", "log-v1"),
            lambda: memory.may_attempt("", "log-v1"),
            lambda: memory.require_attempt_allowed("", "log-v1"),
        ):
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                action()


if __name__ == "__main__":
    unittest.main()
