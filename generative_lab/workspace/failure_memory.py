"""Failure-strategy memory with evidence-sensitive retry gating."""


class FailureMemory:
    def __init__(self):
        self._failures = {}

    @staticmethod
    def _validate_fingerprint(fingerprint):
        if not isinstance(fingerprint, str) or not fingerprint:
            raise ValueError("fingerprint must be a non-empty string")
        return fingerprint

    def record_failure(self, fingerprint, evidence):
        key = self._validate_fingerprint(fingerprint)
        self._failures[key] = str(evidence)

    def may_attempt(self, fingerprint, evidence):
        key = self._validate_fingerprint(fingerprint)
        if key not in self._failures:
            return True
        return self._failures[key] != str(evidence)

    def require_attempt_allowed(self, fingerprint, evidence):
        if not self.may_attempt(fingerprint, evidence):
            raise ValueError(f"failed strategy fingerprint blocked: {fingerprint}")

    def snapshot(self):
        return dict(self._failures)
