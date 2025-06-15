# ========================================
# apps/notes/urls.py - 修正版（ブックマーク・削除機能追加）
# ========================================

from django.urls import path
from apps.notes import views
import apps.notes.help_views  # ヘルプビューをインポート

app_name = 'notes'

urlpatterns = [
    # ノートブック関連
    path('', views.NotebookListView.as_view(), name='list'),
    path('create/', views.NotebookCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.NotebookDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.NotebookUpdateView.as_view(), name='edit'),
    
    # エントリー関連
    path('<uuid:notebook_pk>/entry/create/', views.entry_create_view, name='entry_create'),
    path('entry/<uuid:entry_pk>/', views.entry_detail_ajax, name='entry_detail_ajax'),
    
    # ★ ブックマーク・削除機能
    path('<uuid:pk>/favorite/', views.toggle_favorite_view, name='toggle_favorite'),
    path('entry/<uuid:entry_pk>/bookmark/', views.toggle_entry_bookmark, name='toggle_entry_bookmark'),
    path('entry/<uuid:entry_pk>/delete/', views.delete_entry, name='delete_entry'),
    
    # サブノート関連
    path('<uuid:notebook_pk>/sub-notebook/create/', views.sub_notebook_create_ajax, name='sub_notebook_create'),
    
    # Ajax検索関連
    path('search/', views.notebook_search_ajax, name='search_ajax'),
    path('trending-tags/', views.trending_tags_ajax, name='trending_tags_ajax'),
    path('tag-search/', views.tag_search_ajax, name='tag_search_ajax'),
    path('<uuid:notebook_pk>/entries/search/', views.entry_search_ajax, name='entry_search_ajax'),

    # ヘルプ・検索結果
    path('help/', apps.notes.help_views.NotebookHelpView.as_view(), name='help'),
    path('search/results/', views.NotebookSearchResultsView.as_view(), name='search_results'),
]