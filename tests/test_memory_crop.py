"""SYNTHETIC fixtures for lossless window/boundary selection; no real records."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from swarm_tracer.ai_village import import_ai_village

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("memory_crop", ROOT / "crop_ai_village_memories.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
AGENT = "00000000-0000-4000-8000-000000000001"
OTHER = "00000000-0000-4000-8000-000000000002"
VILLAGE = "00000000-0000-4000-8000-000000000003"
START = "2026-06-01T17:00:00Z"
END = "2026-06-02T21:00:00Z"


def memory(number, stamp, agent=AGENT):
    return {"id": f"10000000-0000-4000-8000-{number:012d}", "agent_id": agent,
        "created_at": stamp, "updated_at": stamp,
        "content": "SYNTHETIC text: $(never_execute); `inert`; accent é"}


class MemoryCropTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "agent_memories.jsonl.gz"
        self.output = self.root / "crop.jsonl.gz"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rows):
        payload = b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)
        self.source.write_bytes(gzip.compress(payload))
        return payload

    def crop(self, **kwargs):
        return MODULE.crop_memories(self.source, self.output, [AGENT], START, END, **kwargs)

    def test_unsorted_source_preserves_nearest_boundaries_and_every_tie(self):
        rows = [memory(1, "2026-06-03 00:00:00"), memory(2, "2026-06-01 16:59:00"),
            memory(3, "2026-06-01 17:00:00"), memory(4, "2026-06-01 16:58:00"),
            memory(5, "2026-06-02 21:00:00"), memory(6, "2026-06-01 16:59:00"),
            memory(7, "2026-06-01 18:00:00", OTHER)]
        self.write(rows)
        report = self.crop()
        result = list(map(json.loads, gzip.decompress(self.output.read_bytes()).splitlines()))
        self.assertEqual({row["id"] for row in result}, {rows[i]["id"] for i in (1, 2, 4, 5)})
        self.assertEqual(report["source_rows"], 7)
        self.assertEqual(report["selected_rows"], 4)
        self.assertEqual(report["source_sha256"], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(report["source_bytes"], self.source.stat().st_size)
        self.assertEqual(report["missing_boundary_context"][AGENT], [])

    def test_missing_boundaries_are_explicit_and_plain_jsonl_supported(self):
        row = memory(1, "2026-06-01 17:05:00")
        payload = self.write([row])
        plain = self.root / "memories.jsonl"
        plain.write_bytes(payload)
        report = MODULE.crop_memories(plain, self.output, [AGENT, OTHER], START, END)
        self.assertEqual(gzip.decompress(self.output.read_bytes()), payload)
        self.assertEqual(report["missing_boundary_context"][AGENT], ["latest-preceding", "earliest-following"])
        self.assertEqual(report["rows_by_agent"][OTHER], 0)

    def test_fractional_times_and_timezone_offsets_select_numerically(self):
        rows = [memory(1, "2026-06-01 16:59:59.999999"),
            memory(2, "2026-06-01T13:00:00-04:00"),
            memory(3, "2026-06-02 20:59:59.999999"), memory(4, "2026-06-02 21:00:00")]
        self.write(rows)
        report = self.crop()
        roles = {row["source_row_id"]: row["selection_role"] for row in report["selection"]}
        self.assertEqual(roles[rows[0]["id"]], "latest-preceding")
        self.assertEqual(roles[rows[1]["id"]], "in-window")
        self.assertEqual(roles[rows[2]["id"]], "in-window")
        self.assertEqual(roles[rows[3]["id"]], "earliest-following")

    def test_corrupt_input_and_row_limit_leave_no_partial_output(self):
        self.write([memory(1, START), memory(2, START)])
        with self.assertRaises(MODULE.CropError):
            self.crop(max_rows=1)
        self.assertFalse(self.output.exists())
        self.assertFalse(Path(str(self.output) + ".selection.json").exists())
        self.source.write_bytes(self.source.read_bytes()[:-4])
        with self.assertRaises((EOFError, OSError)):
            self.crop()
        self.assertFalse(self.output.exists())

    def test_output_overwrite_and_duplicate_selected_ids_are_rejected(self):
        row = memory(1, START)
        self.write([row])
        self.output.write_bytes(b"existing")
        with self.assertRaises(MODULE.CropError):
            self.crop()
        self.assertEqual(self.output.read_bytes(), b"existing")
        self.output.unlink()
        self.write([row, row])
        with self.assertRaises(MODULE.CropError):
            self.crop()
        self.assertFalse(self.output.exists())

    def test_name_resolution_does_not_merge_two_uuid_identities(self):
        agents = self.root / "agents.jsonl"
        agents.write_text("\n".join(json.dumps({"id": i, "name": "SYNTHETIC same label"})
            for i in (AGENT, OTHER)) + "\n")
        with self.assertRaises(MODULE.CropError):
            MODULE.resolve_names(agents, ["SYNTHETIC same label"])
        with self.assertRaises(MODULE.CropError):
            MODULE.resolve_names(agents, ["absent label"])

    def test_crop_reimports_with_boundaries_content_and_updates_preserved(self):
        rows = [memory(1, "2026-06-01 16:59:00"), memory(2, START), memory(3, END)]
        rows[0]["updated_at"] = "2026-06-03 00:00:00"
        self.write(rows)
        report = self.crop()
        agents = self.root / "agents.jsonl"
        agents.write_text(json.dumps({"id": AGENT, "name": "SYNTHETIC Agent", "model_string": "synthetic-model",
            "village_id": VILLAGE, "created_at": START, "updated_at": START}) + "\n")
        evidence = import_ai_village({"agents": agents, "agent_memories": self.output}, synthetic=True)
        self.assertEqual(len(evidence["events"]), 3)
        self.assertEqual(evidence["events"][0]["text"], rows[0]["content"])
        self.assertTrue(evidence["events"][0]["materially_later_update"])
        self.assertEqual(report["selection"][0]["source_row_position"], 2)
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
