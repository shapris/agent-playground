"""Durable in-memory mission state for the generative-coder proof."""

import json


class MissionState:
    STATUSES = frozenset({"DONE", "READY", "BLOCKED"})

    def __init__(self, objectives):
        if not isinstance(objectives, dict):
            raise TypeError("objectives must be a mapping")
        self._objectives = {}
        for objective_id, status in objectives.items():
            self._objectives[str(objective_id)] = self._validate_status(status)

    @classmethod
    def _validate_status(cls, status):
        status = str(status)
        if status not in cls.STATUSES:
            raise ValueError(f"invalid mission status: {status}")
        return status

    def status(self, objective_id):
        return self._objectives[str(objective_id)]

    def transition(self, objective_id, status):
        key = str(objective_id)
        if key not in self._objectives:
            raise KeyError(key)
        self._objectives[key] = self._validate_status(status)

    def to_json(self):
        return json.dumps({"objectives": self._objectives}, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, payload):
        decoded = json.loads(payload)
        if not isinstance(decoded, dict) or set(decoded) != {"objectives"}:
            raise ValueError("mission state JSON must contain only objectives")
        return cls(decoded["objectives"])

    def snapshot(self):
        return dict(self._objectives)
