#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from datetime import date
import json
import re
import sys
import argparse

# =========================
# Data model and IO
# =========================
@dataclass(frozen=True)
class Chunk:
    room_id: str
    room_name: str
    capacity: int
    facilities: Tuple[str, ...]
    area_id: str
    area_name: str
    start: int
    end: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    source: Optional[str] = None

    def pretty(self) -> str:
        fac = "{" + ", ".join(self.facilities) + "}" if self.facilities else "{}"
        return f"{{{self.room_id}, {self.room_name}, {self.capacity}, {fac}, {self.area_id}, {self.area_name}, {self.start}, {self.end}}}"

def find_latest_ready_folder(base: Path) -> Path:
    rx = re.compile(r"^ready_data_(\d{2})-(\d{2})-(\d{4})$")
    candidates = []
    for p in base.iterdir():
        if p.is_dir():
            m = rx.match(p.name)
            if m:
                dd, mm, yyyy = map(int, m.groups())
                try:
                    d = date(yyyy, mm, dd)
                except ValueError:
                    continue
                candidates.append((d, p))
    if not candidates:
        raise FileNotFoundError("No ready_data_dd-mm-yyyy directory found.")
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]

def list_json_files(folder: Path) -> List[Path]:
    return sorted([p for p in folder.glob("*.json") if p.is_file()])

def load_chunks_for_area(ready_dir: Path, area_id: str) -> List[Chunk]:
    chunks: List[Chunk] = []
    files = list_json_files(ready_dir)
    if not files:
        raise FileNotFoundError(f"No .json files in folder: {ready_dir}")

    for fp in files:
        try:
            with fp.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[skip] Failed to parse: {fp.name} -> {e}")
            continue

        vectors = data.get("vectors") if isinstance(data, dict) else None
        if not isinstance(vectors, list):
            print(f"[skip] Non-standard JSON (missing 'vectors' array): {fp.name}")
            continue

        for v in vectors:
            try:
                if str(v.get("area_id")) != str(area_id):
                    continue
                facilities = v.get("facilities") or []
                if isinstance(facilities, str):
                    facilities = [x.strip() for x in re.split(r"[;,/|]", facilities) if x.strip()]
                chunk = Chunk(
                    room_id=str(v.get("room_id", "")),
                    room_name=str(v.get("room_name", "")),
                    capacity=int(v.get("capacity", 0)) if v.get("capacity") not in (None, "") else 0,
                    facilities=tuple(map(str, facilities)),
                    area_id=str(v.get("area_id", "")),
                    area_name=str(v.get("area_name", "")),
                    start=int(v.get("start_index")),
                    end=int(v.get("end_index")),
                    start_time=v.get("start_time"),
                    end_time=v.get("end_time"),
                    source=fp.name
                )
                if chunk.start < chunk.end:
                    chunks.append(chunk)
            except Exception as e:
                print(f"[skip] Invalid or missing vector fields: {fp.name} -> {e}")
                continue
    return chunks

# =========================
# Interval utils and filters
# =========================
def has_required_facilities(chunk: Chunk, required: List[str]) -> bool:
    if not required:
        return True
    have = {f.strip().lower() for f in chunk.facilities}
    need = {f.strip().lower() for f in required if f.strip()}
    return need.issubset(have)

def has_forbidden_facilities(chunk: Chunk, forbidden: List[str]) -> bool:
    if not forbidden:
        return False
    have = {f.strip().lower() for f in chunk.facilities}
    bad = {f.strip().lower() for f in forbidden if f.strip()}
    return any(x in have for x in bad)

def filter_by_facilities(chunks: List[Chunk], required: List[str], forbidden: List[str]) -> List[Chunk]:
    out = []
    for c in chunks:
        if not has_required_facilities(c, required):
            continue
        if has_forbidden_facilities(c, forbidden):
            continue
        out.append(c)
    return out

def area_name_ok(area_name: str, require_contains: List[str], forbid_contains: List[str]) -> bool:
    s = (area_name or "").lower()
    for t in require_contains:
        if t.strip() and t.strip().lower() not in s:
            return False
    for t in forbid_contains:
        if t.strip() and t.strip().lower() in s:
            return False
    return True

def filter_by_area_name(chunks: List[Chunk], require_contains: List[str], forbid_contains: List[str]) -> List[Chunk]:
    return [c for c in chunks if area_name_ok(c.area_name, require_contains, forbid_contains)]

def overlap_len(a: Chunk, b: Chunk) -> int:
    return max(0, min(a.end, b.end) - max(a.start, b.start))

def covers_range_greedy(intervals: List[Tuple[int, int]], s: int, e: int) -> bool:
    if s >= e:
        return True
    ints = sorted(intervals, key=lambda x: (x[0], -x[1]))
    i = 0
    n = len(ints)
    cur = s
    while cur < e:
        max_reach = cur
        while i < n and ints[i][0] <= cur:
            if ints[i][1] > max_reach:
                max_reach = ints[i][1]
            i += 1
        if max_reach == cur:
            return False
        cur = max_reach
    return True

def prune_dominated(chunks: List[Chunk]) -> List[Chunk]:
    sorted_chunks = sorted(chunks, key=lambda c: (c.start, -c.end))
    kept: List[Chunk] = []
    best_end = -10**9
    for c in sorted_chunks:
        if c.end <= best_end:
            continue
        kept.append(c)
        best_end = c.end
    return kept

# =========================
# Solver
# =========================
def zero_change(chunks: List[Chunk], s: int, e: int) -> List[Chunk]:
    hits = [c for c in chunks if c.start <= s and c.end >= e]
    hits.sort(key=lambda c: (c.start, -c.end, c.room_id))
    return hits

def choose_left_best(chunks: List[Chunk], s: int) -> Optional[Chunk]:
    cands = [c for c in chunks if c.start <= s < c.end]
    if not cands:
        return None
    cands.sort(key=lambda c: (c.end, -c.start), reverse=True)
    return cands[0]

def choose_right_best(chunks: List[Chunk], e: int) -> Optional[Chunk]:
    cands = [c for c in chunks if c.start < e and c.end >= e]
    if not cands:
        return None
    cands.sort(key=lambda c: (c.start, -c.end))
    return cands[0]

def one_change(chunks: List[Chunk], s: int, e: int) -> Optional[Tuple[Chunk, Chunk, int]]:
    left = choose_left_best(chunks, s)
    right = choose_right_best(chunks, e)
    if not left or not right:
        return None
    ov = overlap_len(left, right)
    if ov > 0:
        return (left, right, ov)
    return None

def find_straddle_middle(chunks: List[Chunk], left: Chunk, right: Chunk
                        ) -> Optional[Tuple[Chunk, Tuple[int,int], Tuple[int,int]]]:
    b = left.end
    cands = []
    for m in chunks:
        if m is left or m is right:
            continue
        if m.start < b and m.end > b:
            ov1 = overlap_len(left, m)
            ov2 = overlap_len(m, right)
            if ov1 > 0 and ov2 > 0:
                cands.append((m, ov1, ov2))
    if not cands:
        return None

    def score(item):
        m, ov1, ov2 = item
        return (min(ov1, ov2), ov1 + ov2, (m.end - m.start))

    cands.sort(key=score, reverse=True)
    m, ov1, ov2 = cands[0]
    sw1 = (max(left.start, m.start), min(left.end, m.end))
    sw2 = (max(m.start, right.start), min(m.end, right.end))
    return m, sw1, sw2

def two_changes(chunks: List[Chunk], s: int, e: int, allow_three_changes: bool = False
               ) -> Optional[Tuple[List[Chunk], List[Tuple[int, int]]]]:
    left = choose_left_best(chunks, s)
    right = choose_right_best(chunks, e)
    if not left or not right:
        return None

    gap_s, gap_e = left.end, right.start

    if gap_s == gap_e:
        res = find_straddle_middle(chunks, left, right)
        if res:
            middle, sw1, sw2 = res
            return [left, middle, right], [sw1, sw2]
        return [left, right], [(0, 0)]

    if gap_s < gap_e:
        mids = [c for c in chunks if c.start <= gap_s and c.end >= gap_e]
        if mids:
            def score_middle(m: Chunk):
                ov1 = overlap_len(left, m)
                ov2 = overlap_len(m, right)
                return (min(ov1, ov2), (ov1 + ov2), (m.end - m.start))
            mids.sort(key=score_middle, reverse=True)
            middle = mids[0]
            sw1 = (max(left.start, middle.start), min(left.end, middle.end))
            sw2 = (max(middle.start, right.start), min(middle.end, right.end))
            return [left, middle, right], [sw1, sw2]

        if allow_three_changes:
            oc = one_change(chunks, gap_s, gap_e)
            if not oc:
                return None
            mid_left, mid_right, _ = oc
            sw0 = (max(left.start, mid_left.start), min(left.end, mid_left.end))
            sw1 = (max(mid_left.start, mid_right.start), min(mid_left.end, mid_right.end))
            sw2 = (max(mid_right.start, right.start), min(mid_right.end, right.end))
            return [left, mid_left, mid_right, right], [sw0, sw1, sw2]

        return None

    return None

# =========================
# Runner (always prints SUMMARY)
# =========================
def run(area_id: str,
        time_start: int,
        time_end: int,
        required_facilities: List[str],
        forbidden_facilities: List[str],
        require_area_name_contains: List[str],
        forbid_area_name_contains: List[str],
        ready_folder: Optional[str],
        allow_three_changes: bool,
        top_k_zero_change: int) -> Dict[str, Any]:

    base = Path(__file__).resolve().parent
    try:
        ready_dir = Path(ready_folder).resolve() if ready_folder else find_latest_ready_folder(base)
    except Exception as e:
        print(f"[error] Locate ready_ dir failed: {e}")
        summary = {"area_id": area_id, "ok": False, "err": str(e)}
        print("SUMMARY " + json.dumps(summary, ensure_ascii=False))
        return summary

    print(f"Reading ready dir: {ready_dir}")

    chunks_all = load_chunks_for_area(ready_dir, area_id)
    if not chunks_all:
        msg = f"[end] No vectors found for area_id={area_id} in {ready_dir.name}."
        print(msg)
        summary = {"area_id": area_id, "ok": False, "message": msg}
        print("SUMMARY " + json.dumps(summary, ensure_ascii=False))
        return summary

    # Filters
    chunks = filter_by_facilities(chunks_all, required_facilities, forbidden_facilities)
    if require_area_name_contains or forbid_area_name_contains:
        chunks = filter_by_area_name(chunks, require_area_name_contains, forbid_area_name_contains)

    print(f"Candidate vectors after filters: {len(chunks)}")
    coverable = covers_range_greedy([(c.start, c.end) for c in chunks], time_start, time_end)
    if not coverable:
        msg = f"[not satisfiable] Combined rooms cannot cover [{time_start}, {time_end})."
        print(msg)
        summary = {"area_id": area_id, "ok": False, "message": msg}
        print("SUMMARY " + json.dumps(summary, ensure_ascii=False))
        return summary

    pruned = prune_dominated(chunks)
    print(f"After removing dominated intervals: {len(pruned)} (from {len(chunks)})")

    def chunk_to_seg(c: Chunk) -> Dict[str, Any]:
        return {
            "room_id": c.room_id,
            "room_name": c.room_name,
            "capacity": c.capacity,
            "area_id": c.area_id,
            "area_name": c.area_name,
            "start": c.start,
            "end": c.end,
            "start_time": c.start_time,
            "end_time": c.end_time,
            "source": c.source,
        }

    # 0-change
    zc = zero_change(pruned, time_start, time_end)
    if zc:
        print(f"\n[0 changes] Any of the following can satisfy (showing first {top_k_zero_change}):")
        for i, c in enumerate(zc[:top_k_zero_change], 1):
            print(f"  #{i} {c.pretty()}  source:{c.source}")
        if len(zc) > top_k_zero_change:
            print(f"  ...({len(zc)-top_k_zero_change} more not shown)")
        summary = {"area_id": area_id, "ok": True, "changes": 0, "segments": [chunk_to_seg(c) for c in zc[:top_k_zero_change]]}
        print("SUMMARY " + json.dumps(summary, ensure_ascii=False))
        return summary

    # 1-change
    oc = one_change(pruned, time_start, time_end)
    if oc:
        left, right, ov = oc
        sw = (max(left.start, right.start), min(left.end, right.end))
        print("\n[1 change] Feasible plan found (segments overlap):")
        print(f"  Left  : {left.pretty()}  source:{left.source}")
        print(f"  Right : {right.pretty()}  source:{right.source}")
        print(f"  Switch window (slots): [{sw[0]}, {sw[1]}), length {ov}")
        summary = {
            "area_id": area_id,
            "ok": True,
            "changes": 1,
            "segments": [chunk_to_seg(left), chunk_to_seg(right)],
            "switches": [list(sw)]
        }
        print("SUMMARY " + json.dumps(summary, ensure_ascii=False))
        return summary
    else:
        print("\n[info] No 1-change overlapping solution. Trying 2-changes (with tangent redundancy).")

    # 2-changes
    tc = two_changes(pruned, time_start, time_end, allow_three_changes=allow_three_changes)
    if tc:
        plan, switches = tc
        print(f"\n[{len(plan)-1} changes] Feasible plan found:")
        for idx, seg in enumerate(plan, 1):
            print(f"  Seg{idx}: {seg.pretty()}  source:{seg.source}")
        for i, (s, e) in enumerate(switches, 1):
            length = max(0, e - s)
            if length > 0:
                print(f"  Switch window {i}: [{s}, {e}), length {length}")
            else:
                print(f"  Switch window {i}: none (exact boundary switch only)")

        summary = {
            "area_id": area_id,
            "ok": True,
            "changes": len(plan)-1,
            "segments": [chunk_to_seg(seg) for seg in plan],
            "switches": [list(x) for x in switches]
        }

        if len(plan) == 3 and plan[0].end == plan[2].start:
            b = plan[0].end
            print("\n[alternative] Fewer changes via exact boundary switch:")
            print(f"  Left  : {plan[0].pretty()}  source:{plan[0].source}")
            print(f"  Right : {plan[2].pretty()}  source:{plan[2].source}")
            print(f"  Switch at slot index: {b} (no overlap)")
            summary["alternatives"] = [
                {
                    "changes": 1,
                    "segments": [chunk_to_seg(plan[0]), chunk_to_seg(plan[2])],
                    "switch_point": b,
                    "note": "Exact boundary switch, no overlap."
                }
            ]

        print("SUMMARY " + json.dumps(summary, ensure_ascii=False))
        return summary

    msg = ("[not found] No feasible combination under 0/1/2 changes. "
           f"(Try relaxing the time range or enabling allow_three_changes)")
    print(msg)
    summary = {"area_id": area_id, "ok": False, "message": msg}
    print("SUMMARY " + json.dumps(summary, ensure_ascii=False))
    return summary


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Study room planner sub-process")
    ap.add_argument("--area-id", required=True, help="Target area_id")
    ap.add_argument("--start-slot", type=int, required=True, help="Start slot index (inclusive)")
    ap.add_argument("--end-slot", type=int, required=True, help="End slot index (exclusive)")
    ap.add_argument("--required-facilities", default="", help="Required facilities, separated by ';'")
    ap.add_argument("--forbidden-facilities", default="", help="Forbidden facilities, separated by ';'")
    ap.add_argument("--require-area-names", default="", help="Area name must contain (ALL), separated by ';'")
    ap.add_argument("--forbid-area-names", default="", help="Area name must NOT contain (ANY), separated by ';'")
    ap.add_argument("--ready-folder", default="", help="ready_data folder path (leave empty to auto-find latest)")
    ap.add_argument("--allow-three-changes", action="store_true", help="Allow 3 changes (4 segments)")
    ap.add_argument("--top-k-zero-change", type=int, default=50, help="How many 0-change rows to show at most")
    return ap.parse_args()

def main():
    args = parse_args()
    req_fac = [x.strip() for x in args.required_facilities.split(";") if x.strip()]
    forb_fac = [x.strip() for x in args.forbidden_facilities.split(";") if x.strip()]
    req_area = [x.strip() for x in args.require_area_names.split(";") if x.strip()]
    forb_area = [x.strip() for x in args.forbid_area_names.split(";") if x.strip()]
    ready = args.ready_folder.strip() or None

    run(
        area_id=str(args.area_id),
        time_start=int(args.start_slot),
        time_end=int(args.end_slot),
        required_facilities=req_fac,
        forbidden_facilities=forb_fac,
        require_area_name_contains=req_area,
        forbid_area_name_contains=forb_area,
        ready_folder=ready,
        allow_three_changes=bool(args.allow_three_changes),
        top_k_zero_change=int(args.top_k_zero_change)
    )

if __name__ == "__main__":
    main()
