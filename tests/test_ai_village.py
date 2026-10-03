"""SYNTHETIC AI Village fixtures: schema tests, never demo evidence/findings."""

import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from swarm_tracer.ai_village import AdapterError, import_ai_village, parse_utc_timestamp


AGENT = "00000000-0000-4000-8000-000000000001"
SECOND_AGENT = "00000000-0000-4000-8000-000000000002"
VILLAGE = "00000000-0000-4000-8000-000000000003"
SESSION = "00000000-0000-4000-8000-000000000004"
MESSAGE = "00000000-0000-4000-8000-000000000005"
MEMORY = "00000000-0000-4000-8000-000000000006"
TURN = "00000000-0000-4000-8000-000000000007"
ROOM = "00000000-0000-4000-8000-000000000008"
MISSING = "00000000-0000-4000-8000-000000000009"
STAMP = "2026-06-01 12:34:56.123456"


def agent(identity=AGENT, name="SYNTHETIC Agent Alpha"):
    return {"id": identity, "name": name, "model_string": "synthetic-test-model",
        "village_id": VILLAGE, "created_at": STAMP, "updated_at": STAMP}


def message(identity=MESSAGE, speaker=AGENT, stamp=STAMP):
    return {"id": identity, "speaker_type": "agent", "agent_speaker_id": speaker,
        "user_speaker_id": None, "room_id": ROOM, "content": "SYNTHETIC claim, not a real finding.",
        "created_at": stamp, "updated_at": stamp}


def session():
    return {"id": SESSION, "agent_id": AGENT, "village_id": VILLAGE,
        "session_goal": "SYNTHETIC intention", "created_at": STAMP, "updated_at": STAMP}


def turn(response=None):
    return {"id": TURN, "session_id": SESSION, "agent_action": {"command": "SYNTHETIC inert command"},
        "agent_messages": response if response is not None else {"content": [{"type": "text", "text": "SYNTHETIC narration"}]},
        "output": "SYNTHETIC tool output", "error": None, "system": None,
        "screenshot_is_redacted": True, "has_redaction_been_overruled": None,
        "created_at": STAMP, "updated_at": STAMP}


class AiVillageAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.files = {"agents": self.write("agents", [agent()])}

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, table, rows, compressed=False):
        path = self.root / (table + (".jsonl.gz" if compressed else ".jsonl"))
        payload = "".join(json.dumps(row) + "\n" for row in rows).encode()
        path.write_bytes(gzip.compress(payload) if compressed else payload)
        return path

    def import_data(self, **kwargs):
        return import_ai_village(self.files, synthetic=True, **kwargs)

    def test_documented_naive_timestamp_is_utc_with_microseconds(self):
        self.assertEqual(parse_utc_timestamp(STAMP).isoformat(), "2026-06-01T12:34:56.123456+00:00")
        self.assertEqual(parse_utc_timestamp("2026-06-01 12:34:56.123").microsecond, 123000)

    def test_exact_second_sorts_before_later_fractional_second(self):
        earlier = message(MEMORY, stamp="2026-06-01 12:00:00")
        later = message(MESSAGE, stamp="2026-06-01 12:00:00.000001")
        self.files["chat_messages"] = self.write("chat_messages", [later, earlier])
        evidence = self.import_data()
        self.assertEqual([event["source_revision_id"] for event in evidence["events"]], [MEMORY, MESSAGE])

    def test_malformed_or_date_only_row_timestamp_rejected(self):
        for value in ("yesterday", "2026-06-01", None):
            with self.subTest(value=value), self.assertRaises(AdapterError):
                parse_utc_timestamp(value)

    def test_chat_identity_and_source_provenance_are_explicit(self):
        self.files["chat_messages"] = self.write("chat_messages", [message()], compressed=True)
        evidence = self.import_data()
        record = evidence["events"][0]
        self.assertEqual(record["actor_id"], AGENT)
        self.assertEqual(record["event_type"], "chat_message")
        self.assertEqual(record["room_id"], ROOM)
        self.assertEqual(record["provenance"]["source_row_id"], MESSAGE)
        self.assertEqual(record["provenance"]["row_position"], 1)
        self.assertEqual(len(record["provenance"]["row_sha256"]), 64)
        self.assertEqual(len(record["provenance"]["source_file_sha256"]), 64)
        self.assertEqual(record["provenance"]["updated_at"], STAMP)
        self.assertIsNone(record["source_url"])
        self.assertTrue(evidence["dataset"]["synthetic"])
        self.assertEqual(evidence["dataset"]["dataset_revision"], "unknown")
        self.assertEqual(evidence["edges"], [])

    def test_missing_or_ambiguous_agent_link_rejected(self):
        for bad in (message(speaker=MISSING), {**message(), "user_speaker_id": MISSING}, {**message(), "agent_speaker_id": None}):
            self.files["chat_messages"] = self.write("chat_messages", [bad])
            with self.subTest(bad=bad), self.assertRaises(AdapterError):
                self.import_data()

    def test_duplicate_display_names_do_not_collapse_uuid_identity(self):
        self.files["agents"] = self.write("agents", [agent(), agent(SECOND_AGENT, "SYNTHETIC Agent Alpha")])
        self.files["chat_messages"] = self.write("chat_messages", [message(), message(MEMORY, SECOND_AGENT)])
        evidence = self.import_data()
        self.assertEqual(evidence["summary"]["actors"], 2)
        self.assertEqual({event["actor_id"] for event in evidence["events"]}, {AGENT, SECOND_AGENT})

    def test_human_message_excluded_without_agent_attribution(self):
        human = {**message(), "speaker_type": "user", "agent_speaker_id": None, "user_speaker_id": MISSING}
        self.files["chat_messages"] = self.write("chat_messages", [human])
        evidence = self.import_data()
        self.assertEqual(evidence["events"], [])
        self.assertEqual(evidence["summary"]["excluded_human_chat_rows"], 1)

    def test_memory_is_snapshot_without_invented_session_or_reset_join(self):
        memory = {"id": MEMORY, "agent_id": AGENT, "content": "SYNTHETIC retained text", "created_at": STAMP, "updated_at": STAMP}
        self.files["agent_memories"] = self.write("agent_memories", [memory])
        self.files["computer_use_sessions"] = self.write("computer_use_sessions", [session()])
        evidence = self.import_data()
        record = next(event for event in evidence["events"] if event["event_type"] == "memory_snapshot")
        self.assertIsNone(record["session_id"])
        self.assertNotIn("session_identity_link", record["provenance"])
        self.assertEqual(evidence["edges"], [])

    def test_later_mutation_preserves_both_times_and_flags_content_chronology(self):
        row = {**message(), "updated_at": "2026-06-02 12:34:56.123456"}
        self.files["chat_messages"] = self.write("chat_messages", [row])
        record = self.import_data()["events"][0]
        self.assertEqual(record["timestamp"], "2026-06-01T12:34:56.123456Z")
        self.assertTrue(record["materially_later_update"])
        self.assertEqual(record["content_time_status"], "unresolved-current-row-updated")
        self.assertEqual(record["provenance"]["updated_at_utc"], "2026-06-02T12:34:56.123456Z")
        self.assertIn("Current content may reflect", record["provenance"]["content_time_warning"])
        self.assertEqual(record["model_metadata_scope"], "export-state; historical model version unverified")

    def test_turn_distinguishes_execution_response_and_output(self):
        response = [{"type": "reasoning", "summary": [{"text": "SYNTHETIC claim"}]}, {"type": "function_call", "name": "test"}]
        self.files["computer_use_sessions"] = self.write("computer_use_sessions", [session()])
        self.files["computer_use_turns"] = self.write("computer_use_turns", [turn(response)], compressed=True)
        evidence = self.import_data()
        records = {event["event_type"]: event for event in evidence["events"]}
        self.assertEqual(set(records), {"session_intention", "executed_action", "model_response", "tool_output"})
        self.assertEqual(records["model_response"]["payload"], response)
        self.assertEqual(records["executed_action"]["payload"], {"command": "SYNTHETIC inert command"})
        self.assertEqual(records["tool_output"]["payload"]["output"], "SYNTHETIC tool output")
        for record in records.values():
            self.assertFalse(record["action_success_verified"])
            self.assertFalse(record["receipt_observed"])
            self.assertFalse(record["causal_uptake_observed"])

    def test_talk_only_turn_is_not_execution(self):
        self.files["computer_use_sessions"] = self.write("computer_use_sessions", [session()])
        self.files["computer_use_turns"] = self.write("computer_use_turns", [{**turn(), "agent_action": None, "output": None}])
        evidence = self.import_data()
        self.assertNotIn("executed_action", {event["event_type"] for event in evidence["events"]})

    def test_turn_session_join_is_required_and_explicit(self):
        self.files["computer_use_turns"] = self.write("computer_use_turns", [turn()])
        with self.assertRaisesRegex(AdapterError, "requires computer_use_sessions"):
            self.import_data()
        self.files["computer_use_sessions"] = self.write("computer_use_sessions", [session()])
        self.files["computer_use_turns"] = self.write("computer_use_turns", [{**turn(), "session_id": MISSING}])
        with self.assertRaisesRegex(AdapterError, "computer_use_turns:1.*unresolved session"):
            self.import_data()

    def test_slicing_retains_parent_metadata_outside_window(self):
        self.files["computer_use_sessions"] = self.write("computer_use_sessions", [{**session(), "created_at": "2026-05-31 12:00:00"}])
        self.files["computer_use_turns"] = self.write("computer_use_turns", [turn()])
        evidence = self.import_data(start="2026-06-01", end="2026-06-02")
        self.assertEqual(evidence["summary"]["outside_window_rows_by_table"]["computer_use_sessions"], 1)
        self.assertEqual({event["actor_id"] for event in evidence["events"]}, {AGENT})
        self.assertNotIn("session_intention", {event["event_type"] for event in evidence["events"]})

    def test_date_window_is_inclusive_start_exclusive_end(self):
        rows = [message(stamp="2026-06-01 00:00:00"), message(MEMORY, stamp="2026-06-02 00:00:00")]
        self.files["chat_messages"] = self.write("chat_messages", rows)
        evidence = self.import_data(start="2026-06-01", end="2026-06-02")
        self.assertEqual(len(evidence["events"]), 1)
        self.assertEqual(evidence["events"][0]["source_revision_id"], MESSAGE)

    def test_conflicting_duplicate_row_is_rejected(self):
        self.files["chat_messages"] = self.write("chat_messages", [message(), {**message(), "content": "SYNTHETIC conflicting update"}])
        with self.assertRaisesRegex(AdapterError, "conflicting duplicate"):
            self.import_data()

    def test_identical_duplicate_row_is_counted_and_not_reemitted(self):
        self.files["chat_messages"] = self.write("chat_messages", [message(), message()])
        evidence = self.import_data()
        self.assertEqual(len(evidence["events"]), 1)
        self.assertEqual(evidence["summary"]["duplicate_rows_by_table"]["chat_messages"], 1)

    def test_untrusted_content_cannot_trigger_code_or_network(self):
        sentinel = self.root / "payload-executed"
        payload = f"SYNTHETIC __import__('pathlib').Path({str(sentinel)!r}).touch(); <script>alert(1)</script> https://invalid.example/payload"
        self.files["chat_messages"] = self.write("chat_messages", [{**message(), "content": payload}])
        with patch("socket.socket", side_effect=AssertionError("Network is forbidden")), patch("subprocess.Popen", side_effect=AssertionError("Execution is forbidden")):
            evidence = self.import_data()
        self.assertFalse(sentinel.exists())
        self.assertEqual(evidence["events"][0]["text"], payload)

    def test_manifest_is_metadata_not_claimed_authentication(self):
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps({"villageId": VILLAGE, "exportedAt": "2026-09-20T13:05:12.097Z", "rowCounts": {"agents": 500}}))
        evidence = self.import_data(manifest_path=manifest, dataset_revision="SYNTHETIC revision")
        self.assertEqual(evidence["dataset"]["manifest_row_counts"]["agents"], 500)
        self.assertEqual(evidence["summary"]["input_rows_by_table"]["agents"], 1)
        self.assertFalse(evidence["dataset"]["official_revision_authenticated"])

    def test_manifest_village_conflict_rejected(self):
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps({"villageId": MISSING, "exportedAt": "2026-09-20T13:05:12.097Z"}))
        with self.assertRaisesRegex(AdapterError, "does not match"):
            self.import_data(manifest_path=manifest)

    def test_event_limit_prevents_unsliced_large_copy(self):
        self.files["computer_use_sessions"] = self.write("computer_use_sessions", [session()])
        self.files["computer_use_turns"] = self.write("computer_use_turns", [turn()])
        with self.assertRaisesRegex(AdapterError, "Selected event limit"):
            self.import_data(max_events=1)

    def test_remote_input_paths_are_rejected(self):
        with self.assertRaisesRegex(AdapterError, "only local"):
            import_ai_village({"agents": "https://invalid.example/agents.jsonl.gz"}, synthetic=True)


if __name__ == "__main__":
    unittest.main()
