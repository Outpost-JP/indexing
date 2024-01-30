from flask import Flask, request, render_template
from markupsafe import escape
import re
import requests
import os
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build 
from googleapiclient.http import BatchHttpRequest
import httplib2
import json
import base64

# Google Indexing APIのスコープを定義
SCOPES = ["https://www.googleapis.com/auth/indexing"]

# 環境変数からBase64エンコードされたサービスアカウントキーを取得
encoded_key = os.getenv("JSON_KEY_FILE_BASE64")

# エンコードされたキーをデコード
decoded_key = base64.b64decode(encoded_key)

# JSON文字列をPythonの辞書に変換
service_account_info = json.loads(decoded_key)

# クレデンシャルを作成
credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scopes=SCOPES)

# Googleサービスをビルド
http = credentials.authorize(httplib2.Http())
service = build('indexing', 'v3', credentials=credentials)

app = Flask(__name__)  # Flaskアプリのインスタンスを作成
api_base_url = os.getenv("API_BASE_URL")  # 環境変数からAPIのベースURLを取得

@app.route('/')  # ルートURLにアクセスがあった場合
def index():
    return render_template('index.html')  # index.htmlをレンダリングして返す

@app.route('/process', methods=['POST'])
def process():
    # 'input'キーでフォームデータからURLを取得
    input_data = request.form['input']
    # URLから投稿IDを取得し、そのID以降の投稿を取得する
    posts = get_posts_after_id(input_data)
    # 取得した投稿データを処理
    processed_data = process_posts(posts)
    # 処理結果を表示する
    return render_template('index.html', processed_data=processed_data)

def process_posts(posts):
    batch = service.new_batch_http_request(callback=insert_event)
    for url in posts:
        # URLのフォーマットを検証（単純な例）
        if url.startswith("http://") or url.startswith("https://"):
            batch.add(service.urlNotifications().publish(
                body={"url": url, "type": "URL_UPDATED"}))
        else:
            print(f"無効なURLがスキップされました: {url}")
    batch.execute()
    return "Processed {} posts".format(len(posts))

def insert_event(request_id, response, exception):
    if exception is not None:
        print(exception)
    else:
        print(response)

def get_posts_after_id(url):
    post_id_regex = r"/(\d+)/?$"
    match = re.search(post_id_regex, url)
    if match:
        after_id = int(match.group(1))
    else:
        return "Invalid URL"
    
    # 投稿APIのエンドポイント
    api_url = f"{api_base_url}/wp-json/wp/v2/posts"

    # 取得する投稿のパラメータ
    params = {
        "per_page": 100,
        "after": after_id
    }

    urls_list = []  # 投稿のURLを保存するリスト

    # 最初の100件を取得
    r = requests.get(api_url, params=params)
    if r.status_code == 200:
        posts = r.json()
        for post in posts:
            urls_list.append(post['link'])  # 各投稿のURLをリストに追加

        # 次のページがあれば取得を続ける
        while r.links.get("next"):
            r = requests.get(r.links["next"]["url"])
            posts = r.json()
            for post in posts:
                urls_list.append(post['link'])  # 各投稿のURLをリストに追加
    else:
        return "Failed to retrieve posts"

    return urls_list

if __name__ == '__main__':
    app.run()
