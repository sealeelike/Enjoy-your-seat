#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import argparse
import shutil
from pathlib import Path
from datetime import date, datetime, timedelta

def find_target_folder(base_dir: Path) -> Path:
    rx = re.compile(r"^data_(\d{2})-(\d{2})-(\d{4})$")
    candidates = []
    for p in base_dir.iterdir():
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
        raise FileNotFoundError("未在当前目录下找到 data_dd-mm-yyyy 格式的文件夹。")
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]

def list_json_files(folder: Path):
    return sorted([p for p in folder.glob("*.json") if p.is_file()])

def parse_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)

def normalize_facilities_to_list(fac):
    if fac is None:
        return []
    if isinstance(fac, list):
        return [str(x).strip() for x in fac if str(x).strip()]
    if isinstance(fac, str):
        parts = re.split(r"[;,/|]", fac)
        return [p.strip() for p in parts if p.strip()]
    return [str(fac).strip()]

def times_to_sorted_list(schedule: dict):
    def to_minutes(hhmm: str) -> int:
        m = re.fullmatch(r"(\d{2}):(\d{2})", hhmm)
        if not m:
            raise ValueError(f"非法时间格式: {hhmm}")
        h, mnt = int(m.group(1)), int(m.group(2))
        return h * 60 + mnt

    times = list(schedule.keys())
    times.sort(key=to_minutes)
    return times

def guess_slot_minutes(times_sorted):
    def to_minutes(hhmm: str) -> int:
        h, m = map(int, hhmm.split(":"))
        return h*60 + m
    if len(times_sorted) < 2:
        return 30
    mins = [to_minutes(t) for t in times_sorted]
    diffs = [b - a for a, b in zip(mins, mins[1:]) if b > a]
    return min(diffs) if diffs else 30

def add_minutes_str(hhmm: str, minutes: int) -> str:
    h, m = map(int, hhmm.split(":"))
    dt = datetime(2000, 1, 1, h, m) + timedelta(minutes=minutes)
    return dt.strftime("%H:%M")

def compress_available(schedule: dict, available_tokens=("available",)):
    times_sorted = times_to_sorted_list(schedule)
    slot_minutes = guess_slot_minutes(times_sorted)
    lower = {t: str(schedule[t]).strip().lower() for t in times_sorted}
    avail_set = set(s.lower() for s in available_tokens)

    intervals = []
    start = None
    for idx, t in enumerate(times_sorted, start=1):
        is_avail = lower[t] in avail_set
        if is_avail and start is None:
            start = idx
        elif (not is_avail) and (start is not None):
            intervals.append((start, idx))
            start = None
    if start is not None:
        intervals.append((start, len(times_sorted) + 1))
    return intervals, times_sorted, slot_minutes

def iter_room_records(data):
    if isinstance(data, dict):
        if "room_id" in data and "schedule" in data:
            yield data
        elif "rooms" in data and isinstance(data["rooms"], list):
            for r in data["rooms"]:
                if isinstance(r, dict) and "room_id" in r and "schedule" in r:
                    yield r
    elif isinstance(data, list):
        for r in data:
            if isinstance(r, dict) and "room_id" in r and "schedule" in r:
                yield r

def to_int_if_numeric(x):
    try:
        if isinstance(x, (int, float)):
            return int(x)
        s = str(x)
        if s.isdigit():
            return int(s)
    except Exception:
        pass
    return x

def make_vector_json(room, facilities_list, start, end, times_sorted, slot_minutes):
    rid = room.get("room_id", "")
    rname = room.get("room_name", "")
    cap = to_int_if_numeric(room.get("capacity", ""))
    aid = room.get("area_id", "")
    aname = room.get("area_name", "")

    start_time = times_sorted[start - 1] if 1 <= start <= len(times_sorted) else None
    if end <= len(times_sorted):
        end_time = times_sorted[end - 1]  # 半开区间右端点的起始时刻
    else:
        end_time = add_minutes_str(times_sorted[-1], slot_minutes)

    return {
        "room_id": rid,
        "room_name": rname,
        "capacity": cap,
        "facilities": facilities_list,
        "area_id": aid,
        "area_name": aname,
        "start_index": start,
        "end_index": end,         # 半开区间 [start, end)
        "start_time": start_time, # 便于人读；下游可忽略
        "end_time": end_time
    }

def make_facilities_braced_str(items):
    items = [str(x).strip() for x in items if str(x).strip()]
    return "{" + ", ".join(items) + "}"

def make_vector_text(room, facilities_list, start, end):
    rid = room.get("room_id", "")
    rname = room.get("room_name", "")
    cap = room.get("capacity", "")
    aid = room.get("area_id", "")
    aname = room.get("area_name", "")
    fac_str = make_facilities_braced_str(facilities_list)
    return f"{{{rid}, {rname}, {cap}, {fac_str}, {aid}, {aname}, {start}, {end}}}"

def process_file(fp: Path, out_format: str):
    try:
        data = parse_json(fp)
    except Exception as e:
        print(f"[跳过] 解析失败: {fp.name} -> {e}")
        return None

    outputs = []
    for room in iter_room_records(data):
        schedule = room.get("schedule")
        if not isinstance(schedule, dict) or not schedule:
            continue
        facilities_list = normalize_facilities_to_list(room.get("facilities"))
        intervals, times_sorted, slot_minutes = compress_available(schedule)
        for s, e in intervals:
            if out_format == "json":
                outputs.append(
                    make_vector_json(room, facilities_list, s, e, times_sorted, slot_minutes)
                )
            else:
                outputs.append(
                    make_vector_text(room, facilities_list, s, e)
                )
    return outputs

def main():
    parser = argparse.ArgumentParser(description="压缩可用时段并输出结果文件")
    parser.add_argument("--format", choices=["json", "vector"], default="json",
                        help="输出格式：json（推荐）或 vector（{room_id,...} 文本行）")
    parser.add_argument("--folder", type=str, default=None,
                        help="指定要处理的 data_dd-mm-yyyy 文件夹路径（默认自动选择最新的）")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    if args.folder:
        folder = Path(args.folder).resolve()
        if not folder.is_dir():
            print(f"指定的文件夹不存在: {folder}")
            return
    else:
        try:
            folder = find_target_folder(base)
        except Exception as e:
            print(f"定位数据文件夹失败：{e}")
            return

    out_root = folder.parent / ("ready_" + folder.name)

    ready_pattern = re.compile(r"^ready_data_\d{2}-\d{2}-\d{4}$")
    for p in folder.parent.iterdir():
        if p.is_dir() and ready_pattern.match(p.name) and p != out_root:
            try:
                shutil.rmtree(p)
                print(f"已删除过期文件夹：{p.name}")
            except Exception as e:
                print(f"删除文件夹失败 {p.name}：{e}")
                
    out_root.mkdir(parents=True, exist_ok=True)
    files = list_json_files(folder)
    if not files:
        print(f"目标文件夹内没有 .json 文件：{folder}")
        return

    print(f"处理文件夹：{folder}")
    print(f"输出到：{out_root}  （文件名保持不变）")
    total_vectors = 0

    for fp in files:
        outputs = process_file(fp, args.format)
        if outputs is None:
            continue

        out_path = out_root / fp.name
        try:
            if args.format == "json":
                content = {"vectors": outputs}
                with out_path.open("w", encoding="utf-8") as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            else:
                # vector 文本行（注意：文件扩展名仍为 .json，但内容不是 JSON）
                with out_path.open("w", encoding="utf-8") as f:
                    for line in outputs:
                        f.write(line + "\n")
            print(f"[完成] {fp.name} -> {out_path.name} （{len(outputs)} 条）")
            total_vectors += len(outputs)
        except Exception as e:
            print(f"[失败] 写出文件: {out_path} -> {e}")

    print(f"全部完成。条目总数：{total_vectors}")

if __name__ == "__main__":
    main()