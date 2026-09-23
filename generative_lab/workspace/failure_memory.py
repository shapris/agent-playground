"""Failure-strategy memory with evidence-sensitive retry gating."""


class FailureMemory:
    def __init__(self):
        self._failures = {}

    def record_failure(self, fingerprint, evidence):
        key = str(fingerprint)
        if not key:
            raise ValueError("fingerprint must not be empty")
        self._failures[key] = str(evidence)

    def may_attempt(self, fingerprint, evidence):
        key = str(fingerprint)
        if key not in self._failures:
            return True
        return self._failures[key] != str(evidence)

    def require_attempt_allowed(self, fingerprint, evidence):
        if not self.may_attempt(fingerprint, evidence):
            raise ValueError(f"failed strategy fingerprint blocked: {fingerprint}")

    def snapshot(self):
        return dict(self._failures)
