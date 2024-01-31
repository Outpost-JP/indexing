# 必要なライブラリをインポート
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

# 環境変数からBase64エンコードされたサービスアカウントキーを取得し、デコードしてJSONに変換
encoded_key = os.getenv("JSON_KEY_FILE_BASE64")
decoded_key = base64.b64decode(encoded_key)
service_account_info = json.loads(decoded_key)

# クレデンシャルを作成し、Googleサービスをビルド
credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scopes=SCOPES)
http = credentials.authorize(httplib2.Http())
service = build('indexing', 'v3', credentials=credentials)

# Flaskアプリのインスタンスを作成し、APIのベースURLを環境変数から取得
app = Flask(__name__)
api_base_url = os.getenv("API_BASE_URL")

# ルートURLにアクセスがあった場合、index.htmlをレンダリングして返す
@app.route('/')
def index():
    return render_template('index.html')

# '/process'エンドポイントにPOSTリクエストがあった場合の処理
@app.route('/process', methods=['POST'])
def process():
    input_data = request.form['input']  # フォームデータからURLを取得
    posts = get_posts_after_id(input_data)  # URLから投稿IDを取得し、そのID以降の投稿を取得
    if isinstance(posts, str):  # エラーメッセージが返された場合
        return posts, 400
    processed_data = process_posts(posts)  # 取得した投稿データを処理
    latest_post_url = posts[-1] if posts else None  # 最新の記事を特定

    if latest_post_url:  # 最新の記事があればIFTTT WebhookにPOSTリクエストを送信
        send_to_ifttt(latest_post_url)

    return processed_data, 200

# 投稿データを処理する関数
def process_posts(posts):
    batch = service.new_batch_http_request(callback=insert_event)
    for url in posts:
        if url.startswith("http://") or url.startswith("https://"):  # URLのフォーマットを検証
            batch.add(service.urlNotifications().publish(
                body={"url": url, "type": "URL_UPDATED"}))
        else:
            print(f"無効なURLがスキップされました: {url}")
    batch.execute()
    return "Processed {} posts".format(len(posts))

# BatchHttpRequestのコールバック関数
def insert_event(request_id, response, exception):
    if exception is not None:
        print(exception)
    else:
        print(response)

# URLから投稿IDを取得し、そのID以降の投稿を取得する関数
def get_posts_after_id(url):
    post_id_regex = r"/(\d+)/?$"
    match = re.search(post_id_regex, url)
    if match:
        after_id = int(match.group(1))
        print(f"after_id: {after_id}")
    else:
        return "Invalid URL"
    # カスタムAPIエンドポイントのURLを変更
    # /wp-json/wp/v2/posts?per_page=100
    api_url = f"{api_base_url}/wp-json/wp/v2/posts?per_page=100"  # カスタムAPIエンドポイントのURL変更済み
    r = requests.get(api_url)  # APIリクエストを送信
    if r.status_code == 200:
        urls_list = r.json()  # APIから直接URLのリストを取得
    else:
        return f"Failed to retrieve posts, status code: {r.status_code}"

    return urls_list

# IFTTT WebhookにPOSTリクエストを送信する関数
def send_to_ifttt(url):
    event = os.getenv("IFTTT_EVENT_NAME")  # IFTTTのイベント名を環境変数から取得
    webhook_key = os.getenv("IFTTT_WEBHOOK_KEY")  # IFTTTのWebhookキーを環境変数から取得
    ifttt_url = f"https://maker.ifttt.com/trigger/{event}/with/key/{webhook_key}"  # IFTTTのWebhook URLを構築
    data = {"value1": url}  # 送信するデータを作成
    requests.post(ifttt_url, json=data)  # IFTTTのWebhookにPOSTリクエストを送信


# アプリケーションのエントリポイント
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # 環境変数からポート番号を取得、デフォルトは8080
    app.run(host='0.0.0.0', port=port)  # アプリケーションを起動