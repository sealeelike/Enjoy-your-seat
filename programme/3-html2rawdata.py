import os
import json
import shutil # <--- 确保导入
from bs4 import BeautifulSoup

def parse_html_to_schedule(html_content: str, area_id: str, area_map: dict) -> list | None:
    # ... (这个核心解析函数保持不变)
    soup = BeautifulSoup(html_content, 'html.parser')
    schedule_table = soup.find('table', id='day_main')
    if not schedule_table: return None
    header_row = schedule_table.find('thead').find('tr')
    rooms_metadata = []
    for th in header_row.find_all('th')[1:]:
        room_data = {}
        link = th.find('a')
        if not link: continue
        room_data['room_id'] = th.get('data-room')
        room_name_full = link.get_text(strip=True)
        capacity_span = link.find('span', class_='capacity')
        if capacity_span:
            capacity_text = capacity_span.text
            room_data['room_name'] = room_name_full.replace(capacity_text, '').strip()
            room_data['capacity'] = int(capacity_text)
        else:
            room_data['room_name'] = room_name_full
            room_data['capacity'] = None
        room_data['facilities'] = link.get('title', '').replace('View Week', '').strip()
        room_data['area_id'] = area_id
        room_data['area_name'] = area_map.get(area_id, "未知区域")
        room_data['schedule'] = {}
        rooms_metadata.append(room_data)
    body_rows = schedule_table.find('tbody').find_all('tr')
    rowspan_counters = [0] * len(rooms_metadata)
    rowspan_booking_names = [None] * len(rooms_metadata) 
    for row in body_rows:
        time_slot = row.find('th').get_text(strip=True)
        all_cells = row.find_all('td')
        cell_cursor = 0
        for room_index in range(len(rooms_metadata)):
            if rowspan_counters[room_index] > 0:
                booking_name = rowspan_booking_names[room_index]
                rooms_metadata[room_index]['schedule'][time_slot] = booking_name
                rowspan_counters[room_index] -= 1
                continue
            if cell_cursor >= len(all_cells): break
            cell = all_cells[cell_cursor]
            if 'new' in cell.get('class', []):
                rooms_metadata[room_index]['schedule'][time_slot] = "Available"
            elif 'booked' in cell.get('class', []):
                booking_link = cell.find('a')
                booking_name = booking_link.get_text(strip=True) if booking_link and booking_link.get_text(strip=True) else "Booked"
                rooms_metadata[room_index]['schedule'][time_slot] = booking_name
                if cell.has_attr('rowspan'):
                    rowspan_value = int(cell['rowspan'])
                    if rowspan_value > 1:
                        rowspan_counters[room_index] = rowspan_value - 1
                        rowspan_booking_names[room_index] = booking_name
            cell_cursor += 1
    return rooms_metadata

def setup_io_directories():
    """
    (已升级) 自动查找最新的输入目录，创建对应的输出目录，并清理旧的输出目录。
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        input_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(d) and d.startswith('pages_')]
        input_dirs.sort(reverse=True)
        latest_input_dir = input_dirs[0]
        
        output_dir_name = latest_input_dir.replace('pages_', 'data_')
        
        # 新增的清理逻辑
        for item in os.listdir(base_dir):
            if item.startswith("data_") and item != output_dir_name:
                full_item_path = os.path.join(base_dir, item)
                if os.path.isdir(full_item_path):
                    print(f"[清理] -> 正在删除过期的data文件夹: {item}")
                    shutil.rmtree(full_item_path)
        
        output_full_path = os.path.join(base_dir, output_dir_name)
        os.makedirs(output_full_path, exist_ok=True)
        
        print(f"[INFO] 输入目录: {latest_input_dir}")
        print(f"[INFO] 输出目录: {output_dir_name}")
        
        return os.path.join(base_dir, latest_input_dir), output_full_path
        
    except IndexError:
        print("[ERROR] 找不到任何 'pages_*' 文件夹。请先运行抓取脚本。")
        return None, None

# ==============================================================================
#  主程序执行块 (逻辑不变)
# ==============================================================================
if __name__ == "__main__":
    print("--- 原始HTML数据处理器 ---")
    input_dir, output_dir = setup_io_directories()
    if not input_dir: exit()
    try:
        with open('area_mapping.json', 'r', encoding='utf-8') as f:
            area_map = json.load(f)
    except FileNotFoundError:
        print("[ERROR] 找不到 'area_mapping.json' 文件。")
        exit()
    available_files = [f for f in os.listdir(input_dir) if f.startswith('area_') and f.endswith('.html')]
    available_ids = sorted([f.replace('area_', '').replace('.html', '') for f in available_files], key=int)
    if not available_ids:
        print("[INFO] 输入目录中没有找到可处理的html文件。")
        exit()
    print("\n可处理的Area ID:", ", ".join(available_ids))
    user_input = input("请输入要处理的Area ID (单个或多个，用逗号/空格分隔), 或输入 'all' 处理全部:\n> ")
    ids_to_process = []
    if user_input.strip().lower() == 'all':
        ids_to_process = available_ids
    else:
        cleaned_input = user_input.replace(',', ' ')
        ids_to_process = [item.strip() for item in cleaned_input.split() if item.strip()]
    if not ids_to_process:
        print("未输入有效的ID，程序退出。")
        exit()
    print(f"\n--- 开始处理 {len(ids_to_process)} 个文件 ---")
    success_count = 0
    fail_count = 0
    for area_id in ids_to_process:
        html_file_path = os.path.join(input_dir, f"area_{area_id}.html")
        if not os.path.exists(html_file_path):
            print(f"  [跳过] -> ID: {area_id:<4} 对应的HTML文件不存在。")
            fail_count += 1
            continue
        print(f"  [处理] -> ID: {area_id:<4} 文件: {html_file_path}")
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        parsed_data = parse_html_to_schedule(html_content, area_id, area_map)
        if parsed_data:
            json_file_path = os.path.join(output_dir, f"area_{area_id}.json")
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            print(f"  [成功] -> ID: {area_id:<4} 结果已保存至 {json_file_path}")
            success_count += 1
        else:
            print(f"  [失败] -> ID: {area_id:<4} 解析HTML时出错。")
            fail_count += 1
    print("\n--- 处理任务完成 ---")
    print(f"总计: {len(ids_to_process)} 个请求")
    print(f"成功: {success_count}")
    print(f"失败/跳过: {fail_count}")
    print("----------------------")