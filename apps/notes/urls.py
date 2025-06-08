# ========================================
# apps/notes/urls.py
# ========================================

from django.urls import path
from apps.notes import views

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
    path('entry/<uuid:entry_pk>/edit/', views.entry_update_view, name='entry_edit'),
    path('entry/<uuid:entry_pk>/delete/', views.entry_delete_view, name='entry_delete'),
]