# ========================================
# apps/notes/urls.py
# ========================================

from django.urls import path
from apps.notes import views

app_name = 'notes'

urlpatterns = [
    path('', views.NotebookListView.as_view(), name='list'),
    path('create/', views.NotebookCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.NotebookDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.NotebookUpdateView.as_view(), name='edit'),
]