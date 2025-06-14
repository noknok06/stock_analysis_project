# ========================================
# apps/notes/urls.py
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
    
    # ★ 新規追加：ブックマーク・お気に入り機能
    path('<uuid:pk>/favorite/', views.toggle_favorite_view, name='toggle_favorite'),
    path('entry/<uuid:entry_pk>/bookmark/', views.toggle_bookmark_view, name='toggle_bookmark'),
    
    # ★ 新規追加：サブノート関連
    path('<uuid:notebook_pk>/sub-notebook/create/', views.sub_notebook_create_ajax, name='sub_notebook_create'),
    
    # ★ 新規追加：Ajax検索関連
    path('search/', views.notebook_search_ajax, name='notebook_search_ajax'),
    path('<uuid:notebook_pk>/entries/search/', views.entry_search_ajax, name='entry_search_ajax'),

    path('help/', apps.notes.help_views.NotebookHelpView.as_view(), name='help'),
]