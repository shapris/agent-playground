import unittest

from generative_lab.workspace.mission_state import MissionState


class MissionStateTests(unittest.TestCase):
    def test_done_ready_blocked_transitions(self):
        state = MissionState({"OBJ-1": "READY", "OBJ-2": "BLOCKED"})
        state.transition("OBJ-1", "DONE")
        state.transition("OBJ-2", "READY")
        self.assertEqual(state.snapshot(), {"OBJ-1": "DONE", "OBJ-2": "READY"})

    def test_json_round_trip_preserves_state(self):
        original = MissionState({"OBJ-2": "READY", "OBJ-1": "DONE"})
        payload = original.to_json()
        restored = MissionState.from_json(payload)
        self.assertEqual(restored.snapshot(), original.snapshot())
        self.assertEqual(restored.to_json(), payload)

    def test_invalid_status_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid mission status"):
            MissionState({"OBJ-1": "RUNNING"})
        state = MissionState({"OBJ-1": "READY"})
        with self.assertRaises(ValueError):
            state.transition("OBJ-1", "UNKNOWN")

    def test_unknown_objective_cannot_be_created_by_transition(self):
        state = MissionState({"OBJ-1": "READY"})
        with self.assertRaises(KeyError):
            state.transition("OBJ-X", "DONE")

    def test_non_string_objective_identifier_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "objective identifiers"):
            MissionState({1: "READY", "1": "BLOCKED"})

    def test_non_string_lookup_identifier_is_rejected(self):
        state = MissionState({"1": "READY"})
        with self.assertRaisesRegex(ValueError, "objective identifiers"):
            state.status(1)


if __name__ == "__main__":
    unittest.main()
