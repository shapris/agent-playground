"""Durable in-memory mission state for the generative-coder proof."""

import json


class MissionState:
    STATUSES = frozenset({"DONE", "READY", "BLOCKED"})

    def __init__(self, objectives):
        if not isinstance(objectives, dict):
            raise TypeError("objectives must be a mapping")
        self._objectives = {}
        for objective_id, status in objectives.items():
            key = self._validate_objective_id(objective_id)
            if key in self._objectives:
                raise ValueError(f"duplicate objective identifier: {key}")
            self._objectives[key] = self._validate_status(status)

    @staticmethod
    def _validate_objective_id(objective_id):
        if not isinstance(objective_id, str) or not objective_id:
            raise ValueError("objective identifiers must be non-empty strings")
        return objective_id

    @classmethod
    def _validate_status(cls, status):
        if not isinstance(status, str) or status not in cls.STATUSES:
            raise ValueError(f"invalid mission status: {status}")
        return status

    def status(self, objective_id):
        key = self._validate_objective_id(objective_id)
        return self._objectives[key]

    def transition(self, objective_id, status):
        key = self._validate_objective_id(objective_id)
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
