# anime/views.py
# anime/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('save/', views.save_review, name='save_review'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
]