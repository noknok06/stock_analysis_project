# ========================================
# apps/tags/urls.py
# ========================================

from django.urls import path
from apps.tags import views, api_views

app_name = 'tags'

urlpatterns = [
    path('', views.TagListView.as_view(), name='list'),
    path('search/', views.tag_search_ajax, name='search_ajax'),
    
    # API エンドポイント
    path('api/search/', api_views.tag_search_api, name='api_search'),
    path('api/create/', api_views.tag_create_api, name='api_create'),
    path('api/suggestions/', api_views.tag_suggestions_api, name='api_suggestions'),
    path('api/popular/', api_views.popular_tags_api, name='api_popular'),
    
]