# anime/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Anime, AnimeReview
import requests
from .services import analyze_anime_synopsis, generate_user_recommendations 

def index(request):
    # 1. Jikan APIから「今期放送中のアニメ」を取得
    now_url = "https://api.jikan.moe/v4/seasons/now"
    now_response = requests.get(now_url)
    anime_list = []
    if now_response.status_code == 200:
        anime_list = now_response.json().get("data", [])
        
    # 2. Jikan APIから「歴代の人気トップアニメ」を取得
    top_url = "https://api.jikan.moe/v4/top/anime"
    top_response = requests.get(top_url)
    top_anime_list = []
    if top_response.status_code == 200:
        top_anime_list = top_response.json().get("data", [])
        
    recommendations = []
    # 3. ログインしている場合のみ自分のレビューと「おすすめ」を取得
    if request.user.is_authenticated:
        reviews = AnimeReview.objects.filter(user=request.user).order_by('-created_at')
        
        # 今期アニメと歴代トップアニメを合体させた候補リストをAIに渡す！
        combined_candidates = anime_list + top_anime_list
        recommendations = generate_user_recommendations(request.user, combined_candidates)
    else:
        reviews = []
        
    context = {
        'reviews': reviews,
        'anime_list': anime_list,
        'top_anime_list': top_anime_list, # 画面に歴代リストも送る
        'recommendations': recommendations, 
    }
    return render(request, 'anime/index.html', context)


@login_required 
def save_review(request):
    if request.method == 'POST':
        mal_id = request.POST.get('mal_id')
        title = request.POST.get('title')
        image_url = request.POST.get('image_url')
        synopsis = request.POST.get('synopsis')
        rating_str = request.POST.get('user_rating')

        try:
            rating = int(rating_str)
        except (ValueError, TypeError):
            rating = 0

        if mal_id and 1 <= rating <= 5:
            anime, created = Anime.objects.get_or_create(
                mal_id=mal_id,
                defaults={
                    'title': title,
                    'image_url': image_url,
                    'synopsis': synopsis,
                }
            )

            AnimeReview.objects.update_or_create(
                user=request.user,
                anime=anime,
                defaults={'rating': rating}
            )

            analyze_anime_synopsis(anime)
            
    return redirect('index')

@login_required
def delete_review(request, review_id):
    if request.method == 'POST':
        # セキュリティ対策：ログインしている本人のレビューかどうかを確認してから削除する
        review = AnimeReview.objects.filter(id=review_id, user=request.user).first()
        if review:
            review.delete()
            
    # 削除が終わったら、トップ画面（index）に戻る
    return redirect('index')