from flask import Flask, request, render_template
from markupsafe import escape
import re
import requests
import os

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
    # 取得した投稿データを処理（ここでは単に文字列に変換しています）
    processed_data = process_posts(posts)
    # 処理結果をクライアントに返す
    return processed_data

def process_posts(posts):
    # 投稿データを処理するダミーの関数（実際の処理はここに実装）
    return "Processed {} posts".format(len(posts))

def get_posts_after_id(url):
    # URLから投稿IDを見つける正規表現
    post_id_regex = r".*\/posts\/(\d+)"
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
    
    urls_dict = {}  # 投稿のURLを保存する辞書

    # 最初の100件を取得
    r = requests.get(api_url, params=params)
    if r.status_code == 200:
        posts = r.json()
        for post in posts:
            urls_dict[post['link']] = 'URL_UPDATED'  # 各投稿のURLを辞書に追加

        # 次のページがあれば取得を続ける
        while r.links.get("next"):
            r = requests.get(r.links["next"]["url"])
            posts = r.json()
            for post in posts:
                urls_dict[post['link']] = 'URL_UPDATED'  # 各投稿のURLを辞書に追加
    else:
        return "Failed to retrieve posts"

    return urls_dict

if __name__ == '__main__':
   app.run()