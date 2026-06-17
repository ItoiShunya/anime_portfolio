# anime/services.py
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from .models import Anime, Genre, Tag, AnimeReview

# ==========================================
# 【重要】ここに取得したGemini APIキーを入力
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# ==========================================

client = genai.Client(api_key=GEMINI_API_KEY)

# --- 1. アニメ保存時に動く「タグ付け分析」機能 ---
class AnimeAnalysis(BaseModel):
    genres: list[str] = Field(description="アニメの主要なジャンル。最大3つ。日本語で出力")
    tags: list[str] = Field(description="アニメの特徴を表す詳細な要素タグ。最大5つ。日本語で出力")

def analyze_anime_synopsis(anime):
    """アニメのあらすじをGeminiに渡し、ジャンルとタグを抽出する"""
    if not anime.synopsis or anime.is_analyzed_by_ai:
        return False

    prompt = f"""
    以下のアニメのあらすじを読み、このアニメを象徴する「ジャンル」と「特徴タグ」を抽出してください。
    【タイトル】: {anime.title}
    【あらすじ】: {anime.synopsis}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnimeAnalysis,
                temperature=0.2,
            ),
        )
        
        result = json.loads(response.text)
        
        for genre_name in result.get('genres', []):
            genre_obj, _ = Genre.objects.get_or_create(name=genre_name)
            anime.genres.add(genre_obj)
            
        for tag_name in result.get('tags', []):
            tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
            anime.tags.add(tag_obj)
            
        anime.is_analyzed_by_ai = True
        anime.save()
        
        print(f"[{anime.title}] のAI分析が完了しました！")
        return True
        
    except Exception as e:
        print(f"Gemini Analysis Error: {e}")
        return False

# --- 2. 画面を開いた時に動く「おすすめ生成」機能 ---
class RecommendationItem(BaseModel):
    title: str = Field(description="おすすめするアニメのタイトル(英語または公式英名)")
    reason: str = Field(description="なぜこのアニメをおすすめするのか、ユーザーの好みの要素（タグ）を交えた具体的な理由")

class RecommendationResult(BaseModel):
    recommendations: list[RecommendationItem] = Field(description="おすすめのアニメ3件")

def generate_user_recommendations(user, candidate_list):
    """ユーザーの高評価アニメの傾向から、候補リスト(今期+歴代)の中でおすすめのものをGeminiに選定させる"""
    liked_reviews = AnimeReview.objects.filter(user=user, rating__gte=4)
    
    if not liked_reviews.exists():
        return []

    liked_tags = set()
    liked_genres = set()
    for review in liked_reviews:
        liked_tags.update(review.anime.tags.values_list('name', flat=True))
        liked_genres.update(review.anime.genres.values_list('name', flat=True))

    reviewed_mal_ids = AnimeReview.objects.filter(user=user).values_list('anime__mal_id', flat=True)

    candidate_text = ""
    candidate_count = 0
    seen_mal_ids = set() # 重複排除用のセット
    
    for item in candidate_list:
        mal_id = item.get('mal_id')
        # すでにレビュー済みの作品、またはすでに候補に入れた作品はスキップ
        if mal_id in reviewed_mal_ids or mal_id in seen_mal_ids:
            continue
            
        title = item.get('title')
        synopsis = item.get('synopsis', '')
        if synopsis:
            candidate_text += f"- タイトル: {title}\n  あらすじ: {synopsis[:100]}...\n"
            seen_mal_ids.add(mal_id)
            candidate_count += 1
            
        if candidate_count >= 25: # 歴代トップも入るため候補数を少し拡大(最大25件)
            break

    if candidate_count == 0:
        return []

    prompt = f"""
    あなたは優秀なアニメソムリエです。
    以下のユーザーの好みを分析し、【おすすめ候補アニメ一覧】の中から、このユーザーが最も気に入りそうなアニメを3つ厳選してください。
    推薦理由は、「ユーザーが好きな〇〇という要素が含まれているため〜」のように納得感のある説明にしてください。

    【ユーザーの好きなジャンル】: {', '.join(liked_genres)}
    【ユーザーの好きな要素(タグ)】: {', '.join(liked_tags)}

    【おすすめ候補アニメ一覧】
    {candidate_text}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RecommendationResult,
                temperature=0.7,
            ),
        )
        result = json.loads(response.text)
        recs = result.get('recommendations', [])

        # AIが選んだタイトルを元に、APIデータから画像と日本語タイトルを復元
        for rec in recs:
            rec_title = rec.get('title')
            rec['title_japanese'] = rec_title
            rec['image_url'] = ""

            for item in candidate_list:
                if item.get('title') == rec_title:
                    if item.get('title_japanese'):
                        rec['title_japanese'] = item.get('title_japanese')
                    if item.get('images') and item.get('images').get('jpg'):
                        rec['image_url'] = item['images']['jpg']['image_url']
                    break
        return recs
        
    except Exception as e:
        print(f"Recommendation Error: {e}")
        return []