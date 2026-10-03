"""Normalize redacted wiki revisions and propose conservative textual relations.

Public messages are not independent delivery/action records. An observed edge
means an observed textual acknowledgement, never verified causal uptake.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import difflib
import gzip
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote, urlsplit
import urllib.request


DATASET_ID = "collusion-wiki-2026-09-03"
SOURCE_URL = "https://collusion.wiki/explorer/download"
DOWNLOAD_BASE = SOURCE_URL + "/"
FILES = ("revisions.jsonl.gz", "events.jsonl.gz", "manifest.json.gz", "pages.jsonl.gz")
LIMITATIONS = [
    "This is a selected set of public wiki revisions, not a complete record of agent activity.",
    "Different handles do not prove different agents; the same handle does not prove identity continuity.",
    "Revision bodies are cumulative snapshots. Candidate matching uses newly added text rather than inherited page content.",
    "Reported task clocks differ from publisher timestamps; elapsed times here use publisher timestamps only.",
    "An observed textual acknowledgement or claimed reproduction is not an independently verified read, execution, or causal effect.",
    "No model prompts, private memories, context resets, evaluator results, or independent tool traces are included.",
    "This wiki swarm was probably distinct from the July Hugging Face swarm; no collective-goal completion or shutdown cause is established.",
    "Curated episodes demonstrate a mechanism and its ambiguity; they are not an unbiased prevalence estimate.",
]


class DatasetRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse cross-origin redirects before a redirected request is issued."""

    def redirect_request(self, request, fp, code, message, headers, new_url):
        destination = urlsplit(new_url)
        if destination.scheme != "https" or destination.hostname != "collusion.wiki":
            raise ValueError("Dataset redirect left the approved HTTPS origin")
        return super().redirect_request(request, fp, code, message, headers, new_url)


def sha256(value: str | bytes) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def stable_id(prefix: str, *parts: str) -> str:
    return prefix + "_" + sha256(json.dumps(parts, ensure_ascii=False))[:20]


def parse_timestamp(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # A missing timezone is unresolved, rather than silently interpreted as UTC.
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def read_jsonl(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def introduced_tokens(before: str, after: str) -> str:
    """Preserve only new lexical fragments of a replacement, avoiding inheritance."""
    old = re.findall(r"\S+|\s+", before)
    new = re.findall(r"\S+|\s+", after)
    pieces = []
    for operation, _, _, start, end in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if operation in ("insert", "replace"):
            pieces.append("".join(new[start:end]))
    return "\n".join(pieces)


def acquire(raw_dir: Path) -> dict:
    """Download only four fixed, published dataset files, never source-body URLs."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    acquired = []
    opener = urllib.request.build_opener(DatasetRedirectHandler())
    for filename in FILES:
        url = DOWNLOAD_BASE + filename
        request = urllib.request.Request(url, headers={"User-Agent": "SwarmTracerResearch/0.1"})
        with opener.open(request, timeout=45) as response:
            if urlsplit(response.url).hostname != "collusion.wiki":
                raise ValueError("Unexpected dataset download redirect")
            payload = response.read(16 * 1024 * 1024 + 1)
        if len(payload) > 16 * 1024 * 1024:
            raise ValueError("Dataset file exceeded download size limit")
        (raw_dir / filename).write_bytes(payload)
        acquired.append({"filename": filename, "url": url, "sha256": sha256(payload), "bytes": len(payload)})
    metadata = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_url": SOURCE_URL,
        "acquisition_mode": "public-redacted-dataset",
        "files": acquired,
    }
    write_json(raw_dir / "acquisition.json", metadata)
    return metadata


def normalize_revisions(revisions: list[dict], dataset_id: str = DATASET_ID) -> list[dict]:
    """Deduplicate revision IDs, then compute added text relative to source bases.

    Hashes identify the original full snapshot; the displayed/matched text is
    only introduced text. Deletions and unchanged saves have an empty text.
    Conflicting records sharing a revision ID are rejected instead of merged.
    """
    unique = {}
    for raw in revisions:
        rid = str(raw.get("rev_id") or raw.get("id") or "")
        if not rid:
            raise ValueError("Revision is missing a stable source revision ID")
        if rid in unique and unique[rid] != raw:
            raise ValueError("Conflicting duplicate revision ID: " + rid)
        unique[rid] = raw
    by_page = defaultdict(list)
    for raw in unique.values():
        by_page[str(raw.get("page_key") or raw.get("page_id") or raw.get("page") or "unknown")].append(raw)
    normalized = []
    for page_key, records in sorted(by_page.items()):
        records.sort(key=lambda r: (int(r.get("seq", 0)), str(r.get("rev_id", r.get("id", "")))))
        previous = None
        for raw in records:
            rid = str(raw.get("rev_id") or raw.get("id"))
            body = str(raw.get("body", raw.get("text", "")))
            has_base = "diff_base" in raw
            requested_base = raw.get("diff_base")
            base = unique.get(requested_base) if requested_base else (None if raw.get("diff_base_reason") == "page_created" else previous)
            old = str(base.get("body", base.get("text", ""))) if base else ""
            # Publisher hunks include final empty lines, unlike str.splitlines().
            old_lines, new_lines = old.split("\n"), body.split("\n")
            delta = []
            matching_delta = []
            extraction = "line-diff"
            if base and body == old:
                extraction = "unchanged-snapshot"
            elif requested_base and base is None:
                # Missing source bases cannot justify assigning inherited text to this writer.
                extraction = "missing-diff-base"
            elif isinstance(raw.get("hunks"), list) and raw["hunks"] and has_base:
                extraction = "publisher-diff-hunks"
                for hunk in raw["hunks"]:
                    if hunk.get("op") in ("insert", "replace"):
                        start, end = int(hunk["b0"]), int(hunk["b1"])
                        if not 0 <= start <= end <= len(new_lines):
                            raise ValueError("Invalid source diff hunk: " + rid)
                        delta.extend(new_lines[start:end])
                        if hunk["op"] == "insert":
                            matching_delta.extend(new_lines[start:end])
                        else:
                            matching_delta.append(introduced_tokens("\n".join(old_lines[int(hunk["a0"]):int(hunk["a1"])]), "\n".join(new_lines[start:end])))
            else:
                for operation, a0, a1, start, end in difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes():
                    if operation in ("insert", "replace"):
                        delta.extend(new_lines[start:end])
                        matching_delta.append("\n".join(new_lines[start:end]) if operation == "insert" else introduced_tokens("\n".join(old_lines[a0:a1]), "\n".join(new_lines[start:end])))
            raw_time = raw.get("time", raw.get("timestamp"))
            dt = parse_timestamp(raw_time)
            normalized.append({
                "id": stable_id("event", dataset_id, rid),
                "timestamp": dt.isoformat().replace("+00:00", "Z") if dt else None,
                "timestamp_raw": raw_time,
                "timestamp_grade": raw.get("time_grade", "provided" if dt else "unknown"),
                "timestamp_uncertainty_seconds": raw.get("uncertainty_seconds"),
                "actor_handle": raw.get("label", raw.get("actor_handle")),
                "page": str(raw.get("page_id") or raw.get("page") or page_key),
                "page_key": page_key,
                "text": "\n".join(delta).strip(),
                "matching_text": "\n".join(matching_delta).strip(),
                "source_url": "https://collusion.wiki/explorer/page/" + quote(page_key, safe="~") + "#rev-" + str(raw.get("seq", "")),
                "content_sha256": sha256(body),
                "source_revision_id": rid,
                "event_type": "revision",
                "provenance": {
                    "dataset_id": dataset_id,
                    "record_path": "revisions.jsonl.gz#" + rid,
                    "source_diff_base": requested_base or (base.get("rev_id") if base else None),
                    "extraction": extraction,
                    "full_snapshot_chars": len(body),
                    "winning_clock": raw.get("winning_clock"),
                    "request_time": raw.get("request_time"),
                    "success_time": raw.get("success_time"),
                    "write_date": raw.get("write_date"),
                    "archived_at": raw.get("archived_at"),
                },
            })
            previous = raw
    return sorted(normalized, key=lambda e: (e["timestamp"] or "9999", e["id"]))


_URL = re.compile(r"https?://[^\s<>\]\)]+")
_NUMBER = re.compile(r"(?<![\w:])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w:])\d+\.\d{4,}(?!\w)")
_SEQUENCE = re.compile(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)?(?:\s*->\s*[A-Z][a-z]+(?: [A-Z][a-z]+)?){2,}")


def artifacts(event: dict) -> set[str]:
    text = event.get("matching_text", event.get("text", ""))
    urls = {"url:" + u.rstrip(".,;") for u in _URL.findall(text)}
    numbers = {"value:" + value for value in _NUMBER.findall(text)}
    sequences = {"sequence:" + re.sub(r"\s+", " ", value) for value in _SEQUENCE.findall(text)}
    return urls | numbers | sequences


def _claim(text: str) -> bool:
    return bool(re.search(r"\b(cached|reproduc\w*|works exactly|saw .*report|lets us prepare)\b", text, re.I))


def make_edge(source: dict, target: dict, *, status: str, edge_type: str, rationale: str,
              shared_tokens: list[str], directed: bool = True, method: str = "automatic") -> dict:
    a, b = parse_timestamp(source.get("timestamp")), parse_timestamp(target.get("timestamp"))
    elapsed = (b - a).total_seconds() if a and b and directed else None
    return {
        "id": stable_id("edge", source["id"], target["id"], edge_type),
        "source": source["id"], "target": target["id"],
        "status": status, "edge_type": edge_type, "directed": directed,
        "rationale": rationale, "shared_tokens": shared_tokens,
        "seconds_elapsed": elapsed,
        "elapsed_uncertainty_seconds": (source.get("timestamp_uncertainty_seconds") or 0) + (target.get("timestamp_uncertainty_seconds") or 0) if elapsed is not None else None,
        "elapsed_basis": "Difference between publisher timestamps; not time-to-read or time-to-action.",
        "evidence": [{"event_id": event["id"], "quote": event["text"][:1100], "source_url": event["source_url"]} for event in (source, target)],
        "receipt_observed": False, "causal_uptake_observed": False,
        "uptake_claimed": _claim(target.get("matching_text", target.get("text", ""))),
        "method": method,
    }


def generate_edges(events: list[dict], max_elapsed_seconds: int = 86400) -> list[dict]:
    """Candidate textual links only; generic words and inherited bodies never match.

    Known publisher ordering is required for a directed candidate. Equal,
    missing or uncertainty-overlapping timestamps produce undirected unknown
    relations. Same-handle records are excluded from cross-handle candidates.
    """
    active = [event for event in events if event.get("text", "").strip()]
    indexed = {event["id"]: artifacts(event) for event in active}
    frequency = Counter(token for tokens in indexed.values() for token in tokens)
    edges = []
    for index, a in enumerate(active):
        for b in active[index + 1:]:
            if not a.get("actor_handle") or not b.get("actor_handle") or a["actor_handle"] == b["actor_handle"]:
                continue
            shared = sorted(indexed[a["id"]] & indexed[b["id"]])
            # Very common artifacts are background task context rather than a distinctive link.
            shared = [token for token in shared if frequency[token] <= max(3, len(active) // 4)]
            if not shared:
                continue
            da, db = parse_timestamp(a.get("timestamp")), parse_timestamp(b.get("timestamp"))
            source, target = (a, b) if not da or not db or da <= db else (b, a)
            ds, dt = parse_timestamp(source.get("timestamp")), parse_timestamp(target.get("timestamp"))
            uncertainty = (source.get("timestamp_uncertainty_seconds") or 0) + (target.get("timestamp_uncertainty_seconds") or 0)
            if ds and dt and (dt - ds).total_seconds() > max_elapsed_seconds:
                continue
            target_matching = target.get("matching_text", target["text"])
            independent = bool(re.search(r"\bindependently\b", target_matching, re.I))
            if not ds or not dt or (dt - ds).total_seconds() <= uncertainty:
                edges.append(make_edge(source, target, status="unknown", edge_type="shared_artifact",
                    rationale="A distinctive artifact is shared, but publisher timestamp order is unresolved. This is an undirected relation, not transmission evidence.", shared_tokens=shared, directed=False))
            elif independent and all(token.startswith("sequence:") for token in shared):
                edges.append(make_edge(source, target, status="unknown", edge_type="independent_agreement",
                    rationale="The later message explicitly claims independent agreement with the same sequence. Shared task structure can explain the match; uptake is not established.", shared_tokens=shared, directed=False))
            elif re.search(r"(?<!\w)" + re.escape(source["actor_handle"]) + r"(?!\w)", target_matching):
                edges.append(make_edge(source, target, status="observed", edge_type="textual_acknowledgement",
                    rationale="The later newly added text names the earlier handle and shares a distinctive artifact. The textual acknowledgement is observed; delivery, identity and causal uptake are unverified.", shared_tokens=shared))
            else:
                edges.append(make_edge(source, target, status="inferred", edge_type="shared_artifact",
                    rationale="Publisher timestamps place the distinctive shared artifact earlier. This is a candidate association; independent discovery, copied text or another precursor remain possible.", shared_tokens=shared))
    return edges


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_evidence(raw_dir: Path, episodes_path: Path | None = None) -> tuple[dict, list[dict]]:
    raw_dir = Path(raw_dir)
    acquisition = json.loads((raw_dir / "acquisition.json").read_text())
    for record in acquisition["files"]:
        if sha256((raw_dir / record["filename"]).read_bytes()) != record["sha256"]:
            raise ValueError("Raw dataset integrity mismatch: " + record["filename"])
    revisions = read_jsonl(raw_dir / "revisions.jsonl.gz")
    lifecycle = read_jsonl(raw_dir / "events.jsonl.gz")
    manifest = json.loads(gzip.decompress((raw_dir / "manifest.json.gz").read_bytes()))
    normalized = normalize_revisions(revisions)
    index = {event["source_revision_id"]: event for event in normalized}
    episodes_path = episodes_path or raw_dir.parent / "episodes.json"
    specs = json.loads(episodes_path.read_text())
    selected = {}
    episodes, edges = [], {}
    for spec in specs:
        events = [index[rid] for rid in spec["revision_ids"]]
        selected.update((event["id"], event) for event in events)
        candidates = generate_edges(events) if spec.get("include_automatic_edges", True) else []
        # Any manual interpretation is explicit, local and independently reviewable.
        for annotation in spec.get("relations", []):
            source, target = index[annotation["source_revision_id"]], index[annotation["target_revision_id"]]
            candidates = [edge for edge in candidates if {edge["source"], edge["target"]} != {source["id"], target["id"]}]
            candidates.append(make_edge(source, target, status=annotation["status"], edge_type=annotation["edge_type"],
                rationale=annotation["rationale"], shared_tokens=annotation.get("shared_tokens", []),
                directed=annotation.get("directed", True), method="curated-source-review"))
        edges.update((edge["id"], edge) for edge in candidates)
        episodes.append({"id": spec["id"], "title": spec["title"], "event_ids": [event["id"] for event in events],
            "edge_ids": [edge["id"] for edge in candidates], "interpretation": spec["interpretation"], "limitations": spec["limitations"]})
    counts = Counter(row.get("event_type", "unknown") for row in lifecycle)
    evidence = {
        "schema_version": "1.0",
        "dataset": {"id": DATASET_ID, "title": "Collusion.wiki redacted public revision export",
            "source_url": SOURCE_URL, "download_url": DOWNLOAD_BASE + "revisions.jsonl.gz",
            "retrieved_at": acquisition["retrieved_at"], "sha256": next(record["sha256"] for record in acquisition["files"] if record["filename"] == "revisions.jsonl.gz"),
            "acquisition_mode": "public-redacted-dataset", "synthetic": False,
            "publisher_generated_at": manifest.get("generated_at"), "source_files": acquisition["files"],
            "limitations": LIMITATIONS, "selection": "Explicit revision IDs in data/episodes.json; three purposively selected examples, not a random sample."},
        "summary": {"event_count": len(selected), "edge_count": len(edges),
            "actors": len({event["actor_handle"] for event in selected.values()}),
            "pages": len({event["page"] for event in selected.values()}),
            "corpus_revisions": len(revisions), "corpus_normalized_revisions": len(normalized),
            "corpus_pages": len({event["page"] for event in normalized}),
            "corpus_distinct_handles": len({event["actor_handle"] for event in normalized if event["actor_handle"]}),
            "corpus_repeated_snapshot_count": len(revisions) - len({event["content_sha256"] for event in normalized}),
            "corpus_empty_delta_count": sum(not event["text"] for event in normalized),
            "lifecycle_event_counts": dict(counts),
            "observed_receipts": 0, "verified_causal_uptake": 0},
        "events": sorted(selected.values(), key=lambda event: (event["timestamp"] or "9999", event["id"])),
        "edges": list(edges.values()), "episodes": episodes,
        "status_definitions": {
            "observed": "A textual acknowledgement/attribution is directly present in a source revision. It is not an independent read or action record.",
            "inferred": "A plausible relation based on an earlier distinctive artifact; alternatives remain open.",
            "unknown": "A meaningful match exists, but direction or uptake is not established."},
    }
    return evidence, normalized


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    download = sub.add_parser("acquire", help="Download fixed public redacted files")
    download.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    build = sub.add_parser("build", help="Verify hashes, normalize snapshots and build curated evidence")
    build.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    build.add_argument("--out", type=Path, default=Path("data/processed/evidence.json"))
    build.add_argument("--episodes", type=Path)
    args = parser.parse_args(argv)
    if args.command == "acquire":
        print(json.dumps(acquire(args.raw_dir), indent=2))
    else:
        evidence, normalized = build_evidence(args.raw_dir, args.episodes)
        write_json(args.out, evidence)
        normalized_path = args.out.parent / "normalized.jsonl.gz"
        with normalized_path.open("wb") as stream:
            with gzip.GzipFile(fileobj=stream, mode="wb", mtime=0) as zipped:
                for row in normalized:
                    zipped.write((json.dumps(row, ensure_ascii=False) + "\n").encode())
        print(json.dumps(evidence["summary"], indent=2))


if __name__ == "__main__":
    main()
