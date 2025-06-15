# ========================================
# apps/tags/urls.py - 改良版タグURL設定
# ========================================

from django.urls import path
from apps.tags import views, api_views

app_name = 'tags'

urlpatterns = [
    # メインビュー
    path('', views.TagListView.as_view(), name='list'),
    path('<int:pk>/edit/', views.TagUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.TagDeleteView.as_view(), name='delete'),
    
    # Ajax エンドポイント
    path('search/', views.tag_search_ajax, name='search_ajax'),
    path('search/legacy/', views.tag_search_ajax_legacy, name='search_ajax_legacy'),
    path('<int:tag_id>/quick-edit/', views.tag_quick_edit_ajax, name='quick_edit_ajax'),
    path('<int:tag_id>/toggle-status/', views.tag_toggle_status_ajax, name='toggle_status_ajax'),
    path('<int:tag_id>/usage-stats/', views.tag_usage_stats_ajax, name='usage_stats_ajax'),
    path('bulk-action/', views.tag_bulk_action_ajax, name='bulk_action_ajax'),
    
    # API エンドポイント（既存）
    path('api/search/', api_views.tag_search_api, name='api_search'),
    path('api/create/', api_views.tag_create_api, name='api_create'),
    path('api/suggestions/', api_views.tag_suggestions_api, name='api_suggestions'),
    path('api/popular/', api_views.popular_tags_api, name='api_popular'),
]