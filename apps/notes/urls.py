# ========================================
# apps/notes/urls.py - 新しいノート構成対応URL設計
# ========================================

from django.urls import path, include
from apps.notes import views

app_name = 'notes'

urlpatterns = [
    # ========================================
    # ノートブック関連URL
    # ========================================
    
    # ノートブック一覧・検索
    path('', views.NotebookListView.as_view(), name='list'),
    path('search/', views.NotebookListView.as_view(), name='search'),
    
    # ノートブック作成（ステップ形式）
    path('create/', views.notebook_template_selection_view, name='template_selection'),
    path('create/<str:template_type>/', views.NotebookCreateView.as_view(), name='create_with_template'),
    path('create/custom/', views.NotebookCreateView.as_view(), name='create_custom'),
    
    # ノートブック詳細・編集・削除
    path('<uuid:pk>/', views.NotebookDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.NotebookUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', views.notebook_delete_view, name='delete'),
    path('<uuid:pk>/archive/', views.notebook_archive_view, name='archive'),
    path('<uuid:pk>/duplicate/', views.notebook_duplicate_view, name='duplicate'),
    
    # ノートブック統計・エクスポート
    path('<uuid:pk>/stats/', views.notebook_stats_view, name='stats'),
    path('<uuid:pk>/export/', views.notebook_export_view, name='export'),
    
    # ========================================
    # サブノート関連URL
    # ========================================
    
    # サブノート管理
    path('<uuid:notebook_pk>/sub/', views.sub_notebook_create_view, name='sub_notebook_create'),
    path('<uuid:notebook_pk>/sub/<uuid:sub_notebook_pk>/', views.sub_notebook_entries_view, name='sub_notebook_detail'),
    path('<uuid:notebook_pk>/sub/<uuid:sub_notebook_pk>/edit/', views.sub_notebook_edit_view, name='sub_notebook_edit'),
    path('<uuid:notebook_pk>/sub/<uuid:sub_notebook_pk>/delete/', views.sub_notebook_delete_view, name='sub_notebook_delete'),
    path('<uuid:notebook_pk>/sub/<uuid:sub_notebook_pk>/reorder/', views.sub_notebook_reorder_view, name='sub_notebook_reorder'),
    
    # ========================================
    # エントリー関連URL
    # ========================================
    
    # エントリー一覧（横断検索）
    path('entries/', views.EntryListView.as_view(), name='entry_list'),
    path('entries/search/', views.EntryListView.as_view(), name='entry_search'),
    path('entries/bookmarks/', views.bookmarked_entries_view, name='bookmarked_entries'),
    
    # エントリー作成
    path('<uuid:notebook_pk>/entry/create/', views.entry_create_view, name='entry_create'),
    path('<uuid:notebook_pk>/entry/quick/', views.entry_quick_create_view, name='entry_quick_create'),
    path('<uuid:notebook_pk>/entry/import/', views.entry_import_view, name='entry_import'),
    
    # エントリー詳細・編集・削除
    path('entry/<uuid:pk>/', views.EntryDetailView.as_view(), name='entry_detail'),
    path('entry/<uuid:pk>/edit/', views.entry_edit_view, name='entry_edit'),
    path('entry/<uuid:pk>/delete/', views.entry_delete_view, name='entry_delete'),
    path('entry/<uuid:pk>/duplicate/', views.entry_duplicate_view, name='entry_duplicate'),
    
    # エントリーアクション
    path('entry/<uuid:pk>/bookmark/', views.entry_bookmark_toggle_view, name='entry_bookmark_toggle'),
    path('entry/<uuid:pk>/move/', views.entry_move_view, name='entry_move'),
    path('entry/<uuid:pk>/relation/', views.entry_relation_view, name='entry_relation'),
    
    # ========================================
    # Ajax API エンドポイント
    # ========================================
    
    # ノートブック Ajax API
    path('api/notebooks/<uuid:pk>/stats/', views.notebook_stats_api, name='api_notebook_stats'),
    path('api/notebooks/<uuid:pk>/entries/', views.notebook_entries_api, name='api_notebook_entries'),
    path('api/notebooks/suggestions/', views.notebook_suggestions_api, name='api_notebook_suggestions'),
    
    # エントリー Ajax API
    path('api/entries/<uuid:pk>/', views.entry_detail_api, name='api_entry_detail'),
    path('api/entries/<uuid:pk>/bookmark/', views.entry_bookmark_api, name='api_entry_bookmark'),
    path('api/entries/quick-create/', views.entry_quick_create_api, name='api_entry_quick_create'),
    path('api/entries/bulk-action/', views.entry_bulk_action_api, name='api_entry_bulk_action'),
    
    # サブノート Ajax API
    path('api/sub-notebooks/', views.sub_notebook_create_api, name='api_sub_notebook_create'),
    path('api/sub-notebooks/<uuid:pk>/reorder/', views.sub_notebook_reorder_api, name='api_sub_notebook_reorder'),
    
    # 検索・フィルター Ajax API
    path('api/search/live/', views.live_search_api, name='api_live_search'),
    path('api/search/advanced/', views.advanced_search_api, name='api_advanced_search'),
    path('api/filter/stocks/', views.stock_filter_api, name='api_stock_filter'),
    
    # ========================================
    # バルク操作・管理
    # ========================================
    
    # バルク操作
    path('bulk/export/', views.bulk_export_view, name='bulk_export'),
    path('bulk/archive/', views.bulk_archive_view, name='bulk_archive'),
    path('bulk/delete/', views.bulk_delete_view, name='bulk_delete'),
    path('bulk/tag/', views.bulk_tag_view, name='bulk_tag'),
    
    # テンプレート・プリセット管理
    path('templates/', views.template_list_view, name='template_list'),
    path('templates/create/', views.template_create_view, name='template_create'),
    path('templates/<uuid:pk>/apply/', views.template_apply_view, name='template_apply'),
    
    # ========================================
    # 分析・レポート
    # ========================================
    
    # 分析レポート
    path('analytics/', views.analytics_dashboard_view, name='analytics'),
    path('analytics/performance/', views.performance_analysis_view, name='performance_analysis'),
    path('analytics/portfolio/', views.portfolio_analysis_view, name='portfolio_analysis'),
    path('analytics/trends/', views.trend_analysis_view, name='trend_analysis'),
    
    # ========================================
    # 設定・プリファレンス
    # ========================================
    
    # ユーザー設定
    path('settings/', views.notes_settings_view, name='settings'),
    path('settings/export/', views.export_settings_view, name='export_settings'),
    path('settings/import/', views.import_settings_view, name='import_settings'),
    path('settings/backup/', views.backup_view, name='backup'),
]

