from django.urls import path
from apps.notes import api_views

app_name = 'notes_api'

urlpatterns = [
    # RESTful API エンドポイント
    path('notebooks/', api_views.NotebookListCreateAPIView.as_view(), name='notebook_list_create'),
    path('notebooks/<uuid:pk>/', api_views.NotebookRetrieveUpdateDestroyAPIView.as_view(), name='notebook_detail'),
    path('notebooks/<uuid:pk>/entries/', api_views.NotebookEntriesAPIView.as_view(), name='notebook_entries'),
    path('notebooks/<uuid:pk>/stats/', api_views.NotebookStatsAPIView.as_view(), name='notebook_stats'),
    
    path('entries/', api_views.EntryListCreateAPIView.as_view(), name='entry_list_create'),
    path('entries/<uuid:pk>/', api_views.EntryRetrieveUpdateDestroyAPIView.as_view(), name='entry_detail'),
    path('entries/<uuid:pk>/bookmark/', api_views.EntryBookmarkAPIView.as_view(), name='entry_bookmark'),
    
    path('sub-notebooks/', api_views.SubNotebookListCreateAPIView.as_view(), name='sub_notebook_list_create'),
    path('sub-notebooks/<uuid:pk>/', api_views.SubNotebookRetrieveUpdateDestroyAPIView.as_view(), name='sub_notebook_detail'),
    
    # 検索・フィルター
    path('search/', api_views.UnifiedSearchAPIView.as_view(), name='unified_search'),
    path('search/suggestions/', api_views.SearchSuggestionsAPIView.as_view(), name='search_suggestions'),
    path('search/autocomplete/', api_views.AutocompleteAPIView.as_view(), name='autocomplete'),
    
    # バルク操作
    path('bulk/notebooks/', api_views.NotebookBulkAPIView.as_view(), name='notebook_bulk'),
    path('bulk/entries/', api_views.EntryBulkAPIView.as_view(), name='entry_bulk'),
    
    # 分析・レポート
    path('analytics/summary/', api_views.AnalyticsSummaryAPIView.as_view(), name='analytics_summary'),
    path('analytics/trends/', api_views.TrendAnalysisAPIView.as_view(), name='trend_analysis'),
    
    # エクスポート・インポート
    path('export/', api_views.ExportAPIView.as_view(), name='export'),
    path('import/', api_views.ImportAPIView.as_view(), name='import'),
]