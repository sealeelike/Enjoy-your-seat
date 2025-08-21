#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# =============== Config ===============
AREA_GROUPS = {
    1: [1, 13, 55, 54, 3, 9, 24, 52, 53, 50, 49, 99],    # north campus - west
    2: [22, 27, 95, 26, 23, 36, 40, 35, 37, 34, 39, 97],  # north campus - east
    3: []  # south campus (fill later)
}

AREA_NAME_OPTIONS = [
    "SIP Campus-Meeting Rooms in Central Building",
    "Foundation Building",
    "Central Building",
    "...(not imported yet)"
]

FACILITY_OPTIONS = [
    "Online meeting available",
    "86 inch MAXHUB",
    "...(not imported yet)"
]

DAY_BASE_HOUR = 8       # slot 1 => 08:00-08:30
DAY_BASE_MINUTE = 0
MIN_SLOT_INDEX = 1

# =============== Utilities ===============
def parse_hhmm(s: str) -> Tuple[int, int]:
    s = s.strip()
    try:
        hh, mm = s.split(":")
        hh = int(hh); mm = int(mm)
        if not (0 <= hh < 24 and 0 <= mm < 60):
            raise ValueError
        return hh, mm
    except Exception:
        raise ValueError(f"Invalid time: {s}. Use HH:MM (e.g., 09:13).")

def floor_to_half_hour(h: int, m: int) -> Tuple[int, int]:
    return (h, 0) if m < 30 else (h, 30)

def slot_index_from_time(h: int, m: int) -> int:
    base_minutes = DAY_BASE_HOUR * 60 + DAY_BASE_MINUTE
    cur_minutes = h * 60 + m
    delta = cur_minutes - base_minutes
    half_hours = delta // 30
    idx = half_hours + 1
    if idx < MIN_SLOT_INDEX:
        idx = MIN_SLOT_INDEX
    return int(idx)

def slot_to_hhmm(idx: int) -> str:
    # Convert slot index -> wall clock time at slot boundary
    minutes = DAY_BASE_HOUR * 60 + DAY_BASE_MINUTE + (idx - 1) * 30
    hh = (minutes // 60) % 24
    mm = minutes % 60
    return f"{hh:02d}:{mm:02d}"

def pick_filters_from_options(options: List[str], title: str) -> Tuple[List[str], List[str]]:
    print(f"\nAvailable {title} keywords:")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    raw_req = input("Enter indices to REQUIRE (comma-separated, empty = none): ").strip()
    raw_forb = input("Enter indices to FORBID  (comma-separated, empty = none): ").strip()

    def parse_sel(raw: str) -> List[str]:
        if not raw:
            return []
        out = []
        for x in raw.split(","):
            x = x.strip()
            if not x:
                continue
            try:
                k = int(x)
                if 1 <= k <= len(options):
                    out.append(options[k-1])
            except:
                pass
        return out

    return parse_sel(raw_req), parse_sel(raw_forb)

def ensure_logs_dir() -> Path:
    p = Path(__file__).resolve().parent / "logs"
    p.mkdir(exist_ok=True)
    return p

def print_progress(current: int, total: int):
    bar_len = 28
    filled = int(bar_len * current / total) if total else bar_len
    bar = "=" * filled + " " * (bar_len - filled)
    sys.stdout.write(f"\rRunning: [{bar}] {current}/{total}")
    sys.stdout.flush()

def run_sub_for_area(area_id: int,
                     start_slot: int,
                     end_slot: int,
                     req_area_names: List[str],
                     forb_area_names: List[str],
                     req_facilities: List[str],
                     forb_facilities: List[str],
                     log_f,
                     ready_folder: str = "",
                     allow_three_changes: bool = False,
                     top_k_zero_change: int = 50) -> Dict[str, Any]:
    py = sys.executable
    sub_path = Path(__file__).resolve().parent / "sub.py"
    cmd = [
        py, str(sub_path),
        "--area-id", str(area_id),
        "--start-slot", str(start_slot),
        "--end-slot", str(end_slot),
        "--required-facilities", ";".join(req_facilities),
        "--forbidden-facilities", ";".join(forb_facilities),
        "--require-area-names", ";".join(req_area_names),
        "--forbid-area-names", ";".join(forb_area_names),
        "--top-k-zero-change", str(top_k_zero_change)
    ]
    if ready_folder:
        cmd += ["--ready-folder", ready_folder]
    if allow_three_changes:
        cmd += ["--allow-three-changes"]

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace"
    )

    summary: Dict[str, Any] = {"area_id": str(area_id), "ok": False}
    sep = "=" * 60
    log_f.write(f"\n{sep}\nAREA {area_id} START\n{sep}\n")
    if proc.stdout is not None:
        for line in proc.stdout:
            log_f.write(line)
            if line.startswith("SUMMARY "):
                try:
                    js = json.loads(line[len("SUMMARY "):].strip())
                    summary = js
                except Exception:
                    pass
    proc.wait()
    log_f.write(f"\n{sep}\nAREA {area_id} END\n{sep}\n")
    log_f.flush()
    return summary

def main():
    print("Select your location:")
    print("  1) north campus - west")
    print("  2) north campus - east")
    print("  3) south campus")
    while True:
        try:
            loc = int(input("Enter 1/2/3: ").strip())
            if loc in (1, 2, 3):
                break
        except Exception:
            pass
        print("Invalid input. Try again.")

    # Time input and mapping
    while True:
        try:
            s_raw = input("Enter start time (HH:MM, e.g., 09:13): ").strip()
            e_raw = input("Enter end time   (HH:MM, e.g., 13:15): ").strip()
            sh, sm = parse_hhmm(s_raw)
            eh, em = parse_hhmm(e_raw)
            sh2, sm2 = floor_to_half_hour(sh, sm)   # floor to 00/30
            eh2, em2 = floor_to_half_hour(eh, em)   # floor to 00/30
            start_slot = slot_index_from_time(sh2, sm2)  # inclusive
            end_slot = slot_index_from_time(eh2, em2)    # exclusive boundary
            if end_slot <= start_slot:
                print("End time must be after start time in half-hour slots. Try again.")
                continue
            print(f"Aligned to half-hour: start {sh2:02d}:{sm2:02d} -> slot {start_slot}, "
                  f"end {eh2:02d}:{em2:02d} -> boundary slot {end_slot}")
            break
        except Exception as e:
            print(e)

    # Filters
    req_area_names, forb_area_names = pick_filters_from_options(AREA_NAME_OPTIONS, "area_name")
    req_facilities, forb_facilities = pick_filters_from_options(FACILITY_OPTIONS, "facilities")

    ready_folder = input("Specify ready_data folder (empty = auto-pick latest): ").strip()
    allow_three_changes = input("Allow 3 changes (y/N): ").strip().lower() in ("y", "yes")

    area_ids = AREA_GROUPS.get(loc, [])
    if not area_ids:
        print("This location has no configured area_ids yet. Please update main.py.")
        return

    # One shared log file per run
    logs_dir = ensure_logs_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"run_{timestamp}.log"
    with log_path.open("w", encoding="utf-8") as log_f:
        # Write run config header
        config = {
            "location_choice": loc,
            "area_ids": area_ids,
            "start_slot": start_slot,
            "end_slot": end_slot,
            "require_area_names": req_area_names,
            "forbid_area_names": forb_area_names,
            "require_facilities": req_facilities,
            "forbid_facilities": forb_facilities,
            "ready_folder": ready_folder or "(auto)",
            "allow_three_changes": allow_three_changes,
        }
        log_f.write("RUN CONFIG:\n" + json.dumps(config, ensure_ascii=False, indent=2) + "\n")

        print("\nRunning...")
        summaries: List[Dict[str, Any]] = []
        total = len(area_ids)
        for i, aid in enumerate(area_ids, 1):
            s = run_sub_for_area(
                area_id=aid,
                start_slot=start_slot,
                end_slot=end_slot,
                req_area_names=req_area_names,
                forb_area_names=forb_area_names,
                req_facilities=req_facilities,
                forb_facilities=forb_facilities,
                log_f=log_f,
                ready_folder=ready_folder,
                allow_three_changes=allow_three_changes,
                top_k_zero_change=50
            )
            summaries.append(s)
            print_progress(i, total)

    print()  # newline after progress bar

    # Final summary (readable and complete)
    print("\n===== Summary =====")
    ok_list = [x for x in summaries if x.get("ok")]
    if not ok_list:
        print("No feasible plans found.")
    else:
        for info in ok_list:
            aid = info.get("area_id")
            chg = info.get("changes")
            segs = info.get("segments") or []
            area_name = segs[0]["area_name"] if segs else ""
            print(f"\narea_id={aid} | area_name={area_name}")

            if chg == 0:
                print(f"- 0 changes: {len(segs)} single-room option(s)")
                for i, s in enumerate(segs, 1):
                    st, et = slot_to_hhmm(int(s['start'])), slot_to_hhmm(int(s['end']))
                    print(f"  Option {i}: {s['room_name']} (cap {s['capacity']})  {st}-{et}  slots [{s['start']}, {s['end']})")
            else:
                print(f"- Plan: {chg} change(s), {len(segs)} segment(s)")
                for j, s in enumerate(segs, 1):
                    st, et = slot_to_hhmm(int(s['start'])), slot_to_hhmm(int(s['end']))
                    print(f"  Seg{j}: {s['room_name']} (cap {s['capacity']})  {st}-{et}  slots [{s['start']}, {s['end']})")
                switches = info.get("switches") or []
                for j, (a, b) in enumerate(switches, 1):
                    print(f"  Switch window {j}: {slot_to_hhmm(int(a))}-{slot_to_hhmm(int(b))}  slots [{a}, {b})")

                alts = info.get("alternatives") or []
                for k, alt in enumerate(alts, 1):
                    a_chg = alt.get("changes")
                    a_segs = alt.get("segments", [])
                    note = alt.get("note", "")
                    print(f"  Alternative {k}: {a_chg} change(s) ({note})")
                    for j, s in enumerate(a_segs, 1):
                        st, et = slot_to_hhmm(int(s['start'])), slot_to_hhmm(int(s['end']))
                        print(f"    Seg{j}: {s['room_name']} (cap {s['capacity']})  {st}-{et}  slots [{s['start']}, {s['end']})")
                    if "switch_point" in alt:
                        sp = alt["switch_point"]
                        print(f"    Switch at: {slot_to_hhmm(int(sp))}  slot {sp}")

    print(f"\nLog saved to: {log_path}")

if __name__ == "__main__":
    main()
