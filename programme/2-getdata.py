import os
import requests
import json
import shutil
from dotenv import load_dotenv
from datetime import date

def fetch_and_save_html(area_id: str, area_name: str, target_date: date, headers: dict, save_dir: str) -> bool:
    base_url = "https://mrbs.xjtlu.edu.cn/index.php"
    params = {
        'view': 'day',
        'view_all': 1,
        'page_date': target_date.isoformat(),
        'area': area_id,
    }
    print(f"  [请求] -> ID: {area_id:<4} 名称: {area_name}...")
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()

        if 'sso.xjtlu.edu.cn' in response.url:
            print(f"  [失败] -> ID: {area_id:<4} Cookie已过期或无效。")
            return False

        file_path = os.path.join(save_dir, f"area_{area_id}.html")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"  [成功] -> ID: {area_id:<4} 数据已保存至 {file_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  [失败] -> ID: {area_id:<4} 网络错误: {e}")
        return False

def setup_directories(today_str: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    today_dir_name = f"pages_{today_str}"
    today_full_path = os.path.join(base_dir, today_dir_name)

    for item in os.listdir(base_dir):
        if item.startswith("pages_") and item != today_dir_name:
            full_item_path = os.path.join(base_dir, item)
            if os.path.isdir(full_item_path):
                print(f"清理过期文件夹: {item}")
                shutil.rmtree(full_item_path)

    os.makedirs(today_full_path, exist_ok=True)
    return today_full_path

if __name__ == "__main__":
    print("--- MRBS数据抓取引擎 ---")

    # 1. 初始化和加载
    load_dotenv()
    auth_cookie = os.getenv('MRBS_COOKIE')
    if not auth_cookie:
        print("错误：未找到Cookie，请先运行auth.py。")
        exit()

    try:
        with open('area_mapping.json', 'r', encoding='utf-8') as f:
            area_map = json.load(f)
    except FileNotFoundError:
        print("错误：找不到 'area_mapping.json' 文件。请先运行 auth.py 生成。")
        exit()

    # 2. 设置目录和日期
    today_obj = date.today()
    today_str_formatted = today_obj.strftime("%d-%m-%Y")
    save_directory = setup_directories(today_str_formatted)
    print(f"数据将保存在: {save_directory}\n")

    # 3. 默认抓取全部
    ids_to_fetch = list(area_map.keys())
    print(f"[默认] 将抓取全部 {len(ids_to_fetch)} 个区域。")

    # 4. 准备请求并开始抓取
    request_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': auth_cookie
    }
    
    print(f"\n--- 开始抓取 {len(ids_to_fetch)} 个区域的数据 ---")
    success_count = 0
    fail_count = 0

    for area_id in ids_to_fetch:
        area_name = area_map.get(area_id, "")
        is_success = fetch_and_save_html(
            area_id=area_id, 
            area_name=area_name,
            target_date=today_obj, 
            headers=request_headers,
            save_dir=save_directory
        )
        if is_success:
            success_count += 1
        else:
            fail_count += 1

    # 5. 打印总结报告
    print("\n--- 抓取任务完成 ---")
    print(f"总计: {len(ids_to_fetch)} 个请求")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print("----------------------")
