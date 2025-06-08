# ========================================
# apps/common/mixins.py
# ========================================

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q

class UserOwnerMixin(LoginRequiredMixin):
    """ユーザー所有者チェックMixin"""
    
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class SearchMixin:
    """検索機能Mixin"""
    search_fields = []
    
    def get_search_query(self):
        """検索クエリを取得"""
        return self.request.GET.get('q', '').strip()
    
    def apply_search(self, queryset):
        """検索フィルターを適用"""
        query = self.get_search_query()
        if query and self.search_fields:
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(q_objects)
        return queryset
