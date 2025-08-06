# 必要なライブラリのインポート
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json
import os
import urllib.request
import requests


# 設定
URL = 'https://jhomes.to-kousya.or.jp/search/jkknet/service/akiyaJyokenDirect'
CHECK_INTERVAL = 180  # 秒
PREVIOUS_CONTENT_FILE = 'prev_content.txt'
LINE_ACCESS_TOKEN = 'Yu31Ihxp9sZRVHyywRch2sg0h3V9+kIKibmb7YT2uuJ6Zh9IlFlzc5EQvQbCtjGg7+AGy4pE1mE9WUjUuMi70XVZ8aOyDpKax7OdIWIcbOVfUVLs98wbVc32kAfhNenQK3sYIvF0CDnYGy0JN5WspwdB04t89/1O/w1cDnyilFU='
#USER_ID = 'U696f84460f74855329d47f1588d014de'
USER_ID = 'U063380621f535f508496214fefee41f9'

def send_line_message(message):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'to': USER_ID,
        'messages': [{
            'type': 'text',
            'text': message
        }]
    }
    response = requests.post(url, headers=headers, json=data)
    print(response.status_code, response.text)

# 前回の住宅名リストを読み込み
def load_previous():
    try:
        with open(PREVIOUS_CONTENT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# 今回の住宅名リストを保存
def save_current(content):
    with open(PREVIOUS_CONTENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

# Webページの主要部分を取得（Selenium使用）
# JavaScriptによる遷移を明示的にトリガーするバージョン
# JavaScriptで開かれる別ウィンドウの中身を取得する対応
# JavaScriptで開かれる別ウィンドウの中身から住宅名を抽出（タイトル行以降に限定）
# JavaScriptで開かれる別ウィンドウの中身から住宅名を抽出（タイトル行以降に限定し、除外キーワードなし）

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


def fetch_page_content():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(options=options)
    driver.get(URL)

    original_window = driver.current_window_handle

    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "こちら"))
        ).click()
        print("[INFO] 『こちら』リンクをクリックしました。")
    except Exception as e:
        print(f"[WARNING] 『こちら』リンクが見つかりませんでした: {e}")

    WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
    new_window = [w for w in driver.window_handles if w != original_window][0]
    driver.switch_to.window(new_window)
    print(f"[INFO] 新しいウィンドウに切り替え: {driver.current_url}")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, 'html.parser')

    result = []
    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 11:
            house_name = cols[1].get_text(strip=True)
            if house_name:
                if house_name == "住宅名":
                    result = []        
                else:
                    result.append(house_name)


    #print("\n===== 住宅名一覧 =====")
    #for name in result:
    #    print(name)
    #print("===== 表示ここまで =====\n")

    return result


## メインループ
if __name__ == '__main__':
    while True:
        print(f"[{datetime.now()}] チェック中...")
        current_list = fetch_page_content()
        previous_list = load_previous()

        if len(previous_list) == 0:
            if len(current_list) > 0:
                save_current(current_list)
                print('[INFO]初回読み込み完了。')
            else:
                print('[INFO]物件なし。')
                continue
        else:
            new_items = list(set(current_list) - set(previous_list))

            if new_items:
                message = '新着住宅名があります'
                for item in new_items: message += '\n'+item
                send_line_message(message)
                save_current(current_list)
                print("通知をLINEに送信しました。", message)
            else:
                print("[INFO] 新着なし。")

        time.sleep(CHECK_INTERVAL)