# ========================================
# apps/notes/services.py
# ========================================

from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.notes.models import Notebook, Entry
from apps.tags.models import Tag

class NotebookService:
    """ノートブック関連のビジネスロジック"""
    
    @staticmethod
    def get_user_notebooks_with_stats(user):
        """ユーザーのノートブックを統計付きで取得"""
        return Notebook.objects.filter(user=user).annotate(
            recent_entries_count=Count(
                'entries',
                filter=Q(entries__created_at__gte=timezone.now() - timedelta(days=30))
            )
        ).prefetch_related('tags')
    
    @staticmethod
    def search_notebooks(user, query, filters=None):
        """ノートブック検索"""
        queryset = Notebook.objects.filter(user=user)
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(subtitle__icontains=query) |
                Q(company_name__icontains=query) |
                Q(investment_reason__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        
        if filters:
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            if filters.get('tags'):
                queryset = queryset.filter(tags__in=filters['tags'])
        
        return queryset.select_related().prefetch_related('tags')