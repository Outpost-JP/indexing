from flask import Flask, request, render_template
from  markupsafe import escape
import re
import requests

app = Flask(__name__)  # Flaskアプリのインスタンスを作成

@app.route('/')  # ルートURLにアクセスがあった場合
def index():
    return render_template('index.html')  # index.htmlをレンダリングして返す


@app.route('/process', methods=['POST'])
def process():
    input_data = request.form['input']
    get_posts_after_id(input_data)
    # ここでinput_dataを使った処理
    
    return "Processed input: {}".format(input_data)

if __name__ == '__main__':
   app.run()

def get_posts_after_id(url):
    # URLから投稿IDを見つける正規表現
    post_id_regex = r".*\/posts\/(\d+)" 
    match = re.search(post_id_regex, url)
    after_id = int(match.group(1))
    
    # 投稿APIのエンドポイント    
    api_url = "https://example.com/wp-json/wp/v2/posts"
    
    # 取得する投稿のパラメータ
    params = {
        "per_page": 100,
        "after": after_id
    }
    
    posts = []
    
    # 最初の100件を取得
    r = requests.get(api_url, params=params)
    posts += r.json()
    
    # 次のページがあれば取得を続ける
    while r.links.get("next"):
        r = requests.get(r.links["next"]["url"])
        posts += r.json()
        
    return posts