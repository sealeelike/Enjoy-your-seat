import os
import re
import json
import time
import html as html_lib
from datetime import date
from dotenv import load_dotenv, set_key

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions

# --- 全局设置 ---
DOTENV_PATH = '.env'
AREA_MAPPING_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'area_mapping.json')

def extract_area_mapping_from_html(html: str) -> dict:
    """
    从HTML中提取 <select name="area"> 内的 <option value="ID">名称</option>。
    返回形如 {"24":"SIP Campus-GF Classrooms in Foundation Building", ...}
    """
    m = re.search(r'<select[^>]*name=["\']area["\'][^>]*>(.*?)</select>', html, flags=re.I | re.S)
    if not m:
        return {}
    select_html = m.group(1)
    options = re.findall(r'<option[^>]*value=["\'](\d+)["\'][^>]*>(.*?)</option>', select_html, flags=re.I | re.S)

    area_map = {}
    for aid, raw_text in options:
        # 去标签、反转义、压缩空白
        text = re.sub(r'<[^>]+>', '', raw_text)
        text = html_lib.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            area_map[aid] = text
    return area_map

def discover_and_save_area_mapping(driver) -> bool:
    """
    在已登录状态下，访问带明确参数的日视图页面，解析区域映射并保存到 area_mapping.json。
    返回是否成功保存。
    """
    today = date.today().isoformat()
    url = f"https://mrbs.xjtlu.edu.cn/index.php?view=day&view_all=1&page_date={today}"
    print("正在加载日视图页面以发现区域列表 ...")
    driver.get(url)

    # 等待页面关键元素出现；若失败也尝试直接解析 page_source
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='area']"))
        )
    except TimeoutException:
        print("警告：未在超时时间内看到区域下拉框，尝试直接解析页面源码。")

    html = driver.page_source
    area_map = extract_area_mapping_from_html(html)

    if not area_map:
        print("错误：未能在页面中解析到任何区域。")
        return False

    with open(AREA_MAPPING_PATH, 'w', encoding='utf-8') as f:
        json.dump(area_map, f, ensure_ascii=False, indent=2)
    print(f"✓ 已发现 {len(area_map)} 个区域并保存至 {AREA_MAPPING_PATH}")
    return True

def main():
    # --- 1. 加载环境变量 ---
    load_dotenv(DOTENV_PATH)
    username = os.getenv('XJTLU_USERNAME')
    password = os.getenv('XJTLU_PASSWORD')

    # --- 2. 初始化 Selenium WebDriver (强制有头模式) ---
    print("正在以【有头模式】启动Chrome浏览器...")
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    
    # 设置不同的等待时间
    wait_long = WebDriverWait(driver, 300) # 5分钟，用于等待用户手动操作
    wait_short = WebDriverWait(driver, 20)  # 20秒，用于等待页面元素加载

    try:
        # --- 3. 导航到登录页 ---
        print("正在访问 MRBS 网站以触发SSO登录...")
        driver.get("https://mrbs.xjtlu.edu.cn/index.php")
        print("等待SSO登录页面加载...")
        
        # 等待关键的表单元素出现
        username_field = wait_short.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Enter Username']"))
        )
        password_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Enter Password']")
        login_button = driver.find_element(By.XPATH, "//button[text()='Sign in']")

        # --- 4. 根据是否存在凭据，执行不同操作 ---
        if username and password:
            print(f"检测到已保存的用户名: {username}")
            print("正在自动填充并登录...")
            username_field.send_keys(username)
            password_field.send_keys(password)
            login_button.click()
        else:
            print("\n" + "="*50)
            print("!!! 首次运行设置 !!!")
            print("1. 请在打开的浏览器窗口中【输入】您的用户名和密码。")
            print("2. 【不要】点击登录按钮。")
            print("3. 输入完成后，回到本窗口，然后按【Enter】键继续...")
            print("="*50)
            input() # 暂停脚本，等待用户按回车

            captured_username = username_field.get_attribute('value')
            captured_password = password_field.get_attribute('value')

            if not captured_username or not captured_password:
                print("\n错误：未能捕获到用户名或密码，请确保您已在浏览器中输入。")
                return

            set_key(DOTENV_PATH, "XJTLU_USERNAME", captured_username)
            set_key(DOTENV_PATH, "XJTLU_PASSWORD", captured_password)
            print(f"\n✓ 凭据已成功捕获并保存到 {DOTENV_PATH} 文件中！")
            
            print("正在为您点击登录按钮...")
            login_button.click()

        # --- 5. 等待用户手动完成两步验证（公共流程） ---
        print("\n" + "="*50)
        print("!!! 用户操作：请在浏览器窗口中完成【两步验证】!!!")
        print("脚本将等待您登录成功，最长等待5分钟...")
        print("="*50 + "\n")

        # 等待登录成功并跳转回目标页面
        wait_long.until(EC.presence_of_element_located((By.ID, "day_main")))
        print("✓ 检测到登录成功！已跳转回 MRBS 主页。")

        # --- 6. 提取并格式化 Cookies ---
        print("正在提取认证 Cookie...")
        all_cookies = driver.get_cookies()
        required_cookies = ['MRBS_SESSID', 'sdp_user_token']
        cookie_parts = [f"{c['name']}={c['value']}" for c in all_cookies if c['name'] in required_cookies]
        final_cookie_string = "; ".join(cookie_parts)

        if not final_cookie_string or len(cookie_parts) < 2:
            print("错误：未能提取到所有关键的 Cookie。")
        else:
            print(f"成功获取到Cookie: {final_cookie_string}")
            set_key(DOTENV_PATH, "MRBS_COOKIE", final_cookie_string)
            print(f"Cookie已成功保存到 {DOTENV_PATH} 文件中。")

            # --- 7. 登录成功后，自动发现并保存区域映射 ---
            try:
                if discover_and_save_area_mapping(driver):
                    print("区域映射已生成并保存在本地。")
                else:
                    print("未能生成区域映射，请稍后在已登录状态下重试。")
            except Exception as e:
                print(f"发现区域映射时出错：{e}")

    except TimeoutException:
        print("\n操作超时！")
        print("可能原因：")
        print("1. 页面加载过慢，或元素定位器已失效。")
        print("2. 您未在5分钟内完成两步验证。")
        print("请检查网络并重试。")
    except Exception as e:
        print(f"\n发生未知错误: {e}")
    
    finally:
        print("\n任务完成。浏览器将在5秒后自动关闭。")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    main()
