# ========================================
# apps/tags/urls.py
# ========================================

from django.urls import path
from apps.tags import views

app_name = 'tags'

urlpatterns = [
    path('', views.TagListView.as_view(), name='list'),
    path('search/', views.tag_search_ajax, name='search_ajax'),
]
