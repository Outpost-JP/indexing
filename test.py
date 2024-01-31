import requests
import re

# ここにWordPressサイトのベースURLを設定
api_base_url = "https://innovatopia.jp"

def get_post_date(post_id):
    api_url = f'{api_base_url}/wp-json/wp/v2/posts/{post_id}'
    response = requests.get(api_url)
    if response.status_code == 200:
        post_data = response.json()
        return post_data['date']
    return None

def get_posts_between_urls(oldest_url, newest_url):
    post_id_regex = r"/(\d+)/?$"
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
    api_url = f'{api_base_url}/wp-json/wp/v2/posts?after={oldest_post_date}&before={newest_post_date}'
    response = requests.get(api_url)

    if response.status_code != 200:
        return "APIからのレスポンスが正常ではありません。"

    posts = response.json()
    post_urls = [post['link'] for post in posts]

    return post_urls

# テスト用のURLを設定
oldest_url = 'https://innovatopia.jp/ai/ai-news/9807/'
newest_url = 'https://innovatopia.jp/ai/ai-news/9820/'

# 関数をテスト
result = get_posts_between_urls(oldest_url, newest_url)
print(result)

