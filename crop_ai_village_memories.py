#!/usr/bin/env python3
"""Extract a local AI Village memory window with preceding/following context.

Python 3.10+; standard library only. No network, login, or source-code execution.
Source JSON bytes are retained. Output is restricted research input, not a finding.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
from uuid import UUID
import zlib

STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})?$")
PILOT_NAMES = ("Claude Opus 4.7", "DeepSeek-V3.2", "Gemini 3.1 Pro")
PILOT_START = "2026-06-01T17:00:00Z"
PILOT_END = "2026-06-02T21:00:00Z"


class CropError(ValueError):
    pass


def timestamp(value):
    if not isinstance(value, str) or not STAMP.fullmatch(value):
        raise CropError("Expected a complete UTC/ISO timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CropError("Invalid timestamp") from exc
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


def identity(value):
    if not isinstance(value, str):
        raise CropError("Expected a UUID string")
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise CropError("Invalid UUID") from exc


class DigestReader(io.RawIOBase):
    """Hash compressed source bytes as the decompressor reads them."""
    def __init__(self, stream):
        super().__init__()
        self.stream = stream
        self.digest = hashlib.sha256()
        self.bytes_read = 0

    def readable(self):
        return True

    def readinto(self, buffer):
        data = self.stream.read(len(buffer))
        buffer[:len(data)] = data
        self.digest.update(data)
        self.bytes_read += len(data)
        return len(data)


def resolve_names(path, names):
    """Resolve exact export-time labels; refuse missing or ambiguous names."""
    found = {name: set() for name in names}
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as stream:
        for position, payload in enumerate(stream, 1):
            if not payload.strip():
                continue
            try:
                row = json.loads(payload)
                if row.get("name") in found:
                    found[row["name"]].add(identity(row.get("id")))
            except (ValueError, AttributeError) as exc:
                raise CropError(f"agents:{position}: invalid metadata row") from exc
    for name, matches in found.items():
        if len(matches) != 1:
            raise CropError(f"Agent label {name!r} resolves to {len(matches)} UUIDs; use --agent-id instead")
    return [next(iter(found[name])) for name in names]


def crop_memories(source, output, agent_ids, start, end, max_rows=10000):
    source, output = Path(source), Path(output)
    report_path = Path(str(output) + ".selection.json")
    agents = sorted({identity(value) for value in agent_ids})
    left, right = timestamp(start), timestamp(end)
    if not agents or left >= right or max_rows < 1:
        raise CropError("Require agent UUIDs, start < end, and a positive row limit")
    if not source.is_file():
        raise CropError("Input file does not exist")
    if source.resolve() in (output.resolve(), report_path.resolve()):
        raise CropError("Output must differ from input")
    if output.exists() or report_path.exists():
        raise CropError("Output or selection report already exists; choose a new --out")
    original_stat = source.stat()
    output.parent.mkdir(parents=True, exist_ok=True)
    before, after = {}, {}
    selected_ids, selected = set(), []
    counts = {agent: 0 for agent in agents}
    row_count = 0
    with tempfile.TemporaryDirectory(prefix=".memory-crop-", dir=output.parent) as temporary:
        temporary = Path(temporary)
        staged = temporary / "memories.jsonl.gz"
        staged_report = temporary / "selection.json"
        with source.open("rb") as raw, staged.open("xb") as target:
            os.chmod(staged, 0o600)
            tracked = DigestReader(raw)
            buffered = io.BufferedReader(tracked)
            stream = gzip.GzipFile(fileobj=buffered, mode="rb") if source.suffix == ".gz" else buffered
            with stream, gzip.GzipFile(fileobj=target, mode="wb", filename="", mtime=0) as destination:
                def emit(item, role):
                    payload, meta = item
                    if meta["source_row_id"] in selected_ids:
                        raise CropError("Duplicate selected memory ID; inspect source before importing")
                    if len(selected) >= max_rows:
                        raise CropError("Selected row limit exceeded; narrow the window or increase --max-rows")
                    selected_ids.add(meta["source_row_id"])
                    selected.append({**meta, "selection_role": role})
                    counts[meta["agent_id"]] += 1
                    destination.write(payload if payload.endswith(b"\n") else payload + b"\n")

                for position, payload in enumerate(stream, 1):
                    if not payload.strip():
                        continue
                    row_count += 1
                    try:
                        row = json.loads(payload)
                        agent = identity(row.get("agent_id"))
                        if agent not in counts:
                            continue
                        created = timestamp(row.get("created_at"))
                        timestamp(row.get("updated_at"))
                        row_id = identity(row.get("id"))
                        if not isinstance(row.get("content"), str):
                            raise CropError("Selected memory content must be text")
                    except (ValueError, AttributeError, UnicodeDecodeError) as exc:
                        raise CropError(f"agent_memories:{position}: malformed row") from exc
                    item = (payload, {"source_row_id": row_id, "agent_id": agent,
                        "source_row_position": position, "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "raw_source_line_sha256": hashlib.sha256(payload).hexdigest()})
                    if left <= created < right:
                        emit(item, "in-window")
                    else:
                        candidates = before if created < left else after
                        best = candidates.get(agent)
                        if best is None or (created > best[0] if created < left else created < best[0]):
                            candidates[agent] = (created, [item])
                        elif created == best[0]:
                            # Preserve every tied nearest snapshot; do not invent ordering.
                            best[1].append(item)
                            if len(best[1]) > max_rows:
                                raise CropError("Too many tied boundary rows")
                for candidates, role in ((before, "latest-preceding"), (after, "earliest-following")):
                    for agent in agents:
                        for item in candidates.get(agent, (None, []))[1]:
                            emit(item, role)
            # End-of-file validates the gzip stream/CRC; no partial output is published.
            source_hash = tracked.digest.hexdigest()
            source_bytes = tracked.bytes_read
        current_stat = source.stat()
        if (current_stat.st_size, current_stat.st_mtime_ns) != (original_stat.st_size, original_stat.st_mtime_ns):
            raise CropError("Input changed during extraction")
        if source_bytes != original_stat.st_size:
            raise CropError("Source was not completely read")
        missing = {agent: [role for role, candidates in (("latest-preceding", before), ("earliest-following", after))
            if agent not in candidates] for agent in agents}
        output_digest = hashlib.sha256()
        with staged.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                output_digest.update(block)
        report = {"access_class": "restricted-research", "source_file": source.name,
            "source_sha256": source_hash, "source_bytes": source_bytes, "source_rows": row_count,
            "output_file": output.name, "output_sha256": output_digest.hexdigest(),
            "output_bytes": staged.stat().st_size, "selected_rows": len(selected),
            "rows_by_agent": counts, "start_inclusive_utc": left.isoformat(),
            "end_exclusive_utc": right.isoformat(), "missing_boundary_context": missing,
            "selection": selected, "limitations": [
                "Selection uses database created_at; updated_at remains preserved and can undermine historical baselines.",
                "Nearest boundary snapshots are selected globally, including timestamp ties; file order is not chronology.",
                "Missing boundaries are reported, not fabricated. No read receipt or causal transmission is inferred.",
                "The report preserves original source row positions/hashes; reimported crop positions differ.",
                "Source JSON bytes are preserved; a missing final newline is added to delimit the output row.",
                "Import this crop separately without start/end filtering to retain boundary context."]}
        staged_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        os.chmod(staged_report, 0o600)
        # Exclusive hard links prevent overwriting existing outputs, including races.
        os.link(staged, output)
        try:
            os.link(staged_report, report_path)
        except OSError:
            output.unlink()
            raise
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Local agent_memories.jsonl.gz or .jsonl")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--agent-id", action="append", default=[])
    parser.add_argument("--agents", type=Path, help="Local agents.jsonl.gz for exact name resolution")
    parser.add_argument("--agent-name", action="append", default=[])
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--calendar-pilot", action="store_true", help="June 1-2 window; resolve three exact export-time agent names")
    parser.add_argument("--max-rows", type=int, default=10000)
    args = parser.parse_args()
    names = args.agent_name or (PILOT_NAMES if args.calendar_pilot else [])
    start = args.start or (PILOT_START if args.calendar_pilot else None)
    end = args.end or (PILOT_END if args.calendar_pilot else None)
    if not start or not end or (names and not args.agents):
        parser.error("Provide --start and --end; name selection also requires --agents")
    output = args.out or args.input.with_name("agent_memories-pilot.jsonl.gz")
    try:
        agents = args.agent_id + (resolve_names(args.agents, names) if names else [])
        report = crop_memories(args.input, output, agents, start, end, args.max_rows)
    except (CropError, OSError, EOFError, zlib.error) as exc:
        parser.exit(1, "Extraction failed: " + str(exc) + "\n")
    print(json.dumps({"output": str(output), "selection_report": str(output) + ".selection.json",
        "source_rows": report["source_rows"], "selected_rows": report["selected_rows"],
        "output_bytes": report["output_bytes"], "missing_boundary_context": report["missing_boundary_context"]}, indent=2))


if __name__ == "__main__":
    main()
