# anime/views.py
# anime/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # トップページ
    path('', views.index, name='index'),
    # レビュー保存
    path('save/', views.save_review, name='save_review'),
    # レビュー削除
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
    
    #サインアップ用のURL
    path('signup/', views.signup, name='signup'),
    
    
]