# 必要なライブラリをインポート
from flask import Flask, request, render_template, jsonify
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

# 例外を定義
class PostRetrievalError(Exception):
    pass

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
    try:
        oldest_url = request.form['firstUrlInput']
        newest_url = request.form['lastUrlInput']
        posts = get_posts_between_urls(oldest_url, newest_url)
        processed_urls, skipped_urls = process_posts(posts)
        send_to_ifttt(newest_url)
        return jsonify({
            "success": True,
            "processed": len(processed_urls),
            "skipped": skipped_urls
        })
    except PostRetrievalError as e:
        return jsonify({"error": str(e)}), 502  # または適切なエラーコード


# 投稿データを処理する関数
def process_posts(posts):
    batch = service.new_batch_http_request(callback=insert_event)
    processed_urls = []
    skipped_urls = []
    for url in posts:
        if url.startswith("http://") or url.startswith("https://"):  # URLのフォーマットを検証
            batch.add(service.urlNotifications().publish(
                body={"url": url, "type": "URL_UPDATED"}))
            processed_urls.append(url)
        else:
            print(f"無効なURLがスキップされました: {url}")
            skipped_urls.append(url)
    batch.execute()
    return processed_urls, skipped_urls

# BatchHttpRequestのコールバック関数
def insert_event(request_id, response, exception):
    if exception is not None:
        print(exception)
    else:
        print(response)

def get_post_date(post_id):
    api_url = f'{api_base_url}/wp-json/wp/v2/posts/{post_id}'
    response = requests.get(api_url)
    if response.status_code == 200:
        post_data = response.json()
        return post_data['date']
    return None

def get_posts_between_urls(oldest_url, newest_url):
    post_id_regex = r"/(\d+)/?$"
    # URLから投稿IDを抽出
    oldest_match = re.search(post_id_regex, oldest_url)
    newest_match = re.search(post_id_regex, newest_url)
    if oldest_match and newest_match:
        oldest_id = int(oldest_match.group(1))
        newest_id = int(newest_match.group(1))
    else:
        return "Invalid URL"
    oldest_post_date = get_post_date(oldest_id)
    newest_post_date = get_post_date(newest_id)   

    if not oldest_post_date or not newest_post_date:
        return "日付を取得できませんでした。" 
    api_url = f'{api_base_url}/wp-json/wp/v2/posts?after={oldest_post_date}&before={newest_post_date}&per_page=100'
    response = requests.get(api_url)

    if response.status_code != 200:
        return "APIからのレスポンスが正常ではありません。"

    posts = response.json()
    post_urls = [post['link'] for post in posts]

    return post_urls


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