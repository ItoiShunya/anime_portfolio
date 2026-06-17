import requests


# Jikan API（MyAnimeListのデータ）のエンドポイント
url = "https://api.jikan.moe/v4/anime"

# 検索条件（Frierenで検索、結果は1件だけ取得）
params = {
    "q": "Frieren",
    "limit": 1
}

print("APIにリクエストを送信中...")

# APIにデータを要求（GETリクエスト）
response = requests.get(url, params=params)

# ステータスコード200は「成功」の意味
if response.status_code == 200:
    # 取得したデータをPythonで扱いやすい形式（辞書型）に変換
    data = response.json()
    anime_info = data["data"][0]
    
    print("\n=== データ取得成功！ ===")
    print(f"タイトル(ローマ字): {anime_info['title']}")
    print(f"英語タイトル: {anime_info['title_english']}")
    print(f"評価スコア: {anime_info['score']}")
    print(f"画像URL: {anime_info['images']['jpg']['image_url']}")
    print("========================\n")
else:
    print(f"エラーが発生しました: {response.status_code}")