"""Failure-strategy memory with evidence-sensitive retry gating."""


class FailureMemory:
    def __init__(self):
        self._failures = {}

    @staticmethod
    def _validate_fingerprint(fingerprint):
        if not isinstance(fingerprint, str) or not fingerprint:
            raise ValueError("fingerprint must be a non-empty string")
        return fingerprint

    @staticmethod
    def _validate_evidence(evidence):
        if not isinstance(evidence, str) or not evidence:
            raise ValueError("evidence must be a non-empty string")
        return evidence

    def record_failure(self, fingerprint, evidence):
        key = self._validate_fingerprint(fingerprint)
        evidence_value = self._validate_evidence(evidence)
        self._failures.setdefault(key, set()).add(evidence_value)

    def may_attempt(self, fingerprint, evidence):
        key = self._validate_fingerprint(fingerprint)
        evidence_value = self._validate_evidence(evidence)
        if key not in self._failures:
            return True
        return evidence_value not in self._failures[key]

    def require_attempt_allowed(self, fingerprint, evidence):
        if not self.may_attempt(fingerprint, evidence):
            raise ValueError(f"failed strategy fingerprint blocked: {fingerprint}")

    def snapshot(self):
        return {key: sorted(values) for key, values in self._failures.items()}
