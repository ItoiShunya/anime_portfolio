from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Genre(models.Model):
    """GeminiおよびJikan APIから取得した大まかなジャンル（例: ファンタジー、SF、日常）"""
    name = models.CharField(max_length=50, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.name

class Tag(models.Model):
    """Geminiがコンテキストから抽出した詳細な要素タグ（例: 主人公最強、泣ける、緻密な世界観）"""
    name = models.CharField(max_length=50, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Anime(models.Model):
    """アニメのマスターデータ（今期＋歴代共通）"""
    # Jikan API (MyAnimeList) のID。これを基準に重複チェックを行う
    mal_id = models.IntegerField(unique=True, primary_key=False, db_index=True)
    
    title = models.CharField(max_length=255)
    title_english = models.CharField(max_length=255, blank=True, null=True)
    
    # Jikan APIから取得するあらすじ（Geminiの解析元データ）
    synopsis = models.TextField(blank=True, null=True)
    
    # 画像URLや公式リンク
    image_url = models.URLField(blank=True, null=True)
    
    # 放送時期（例: "2026-Spring", "2011-Autumn"）。ソートやフィルタリングを容易にする形式
    release_season = models.CharField(max_length=20, db_index=True, blank=True, null=True)
    
    # 今期アニメか、歴代アーカイブデータかを識別するフラグ
    is_archived = models.BooleanField(default=False, db_index=True)
    
    # 多対多（Many-to-Many）のリレーション
    genres = models.ManyToManyField(Genre, blank=True, related_name='animes')
    tags = models.ManyToManyField(Tag, blank=True, related_name='animes')
    
    # Geminiによる解析が完了しているかどうかの管理フラグ
    is_analyzed_by_ai = models.BooleanField(default=False, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class AnimeReview(models.Model):
    """ユーザーのマイ・アニメレビュー"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='anime_reviews')
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='reviews')
    
    # 評価（1〜5の星。Djangoのバリデータで制限）
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True
    )
    
    # レビュー本文（任意）
    comment = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # 1人のユーザーが同じアニメに複数回レビューを書けないように制約
        unique_together = ('user', 'anime')

    def __str__(self):
        return f"{self.user.username} - {self.anime.title} ({self.rating})"