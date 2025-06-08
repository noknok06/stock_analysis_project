# ========================================
# apps/tags/views.py
# ========================================

from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import ListView
from django.db.models import Q
from apps.tags.models import Tag

class TagListView(ListView):
    """タグ一覧ビュー"""
    model = Tag
    template_name = 'tags/list.html'
    context_object_name = 'tags'
    paginate_by = 50
    
    def get_queryset(self):
        """アクティブなタグのみ取得"""
        return Tag.objects.filter(is_active=True).order_by('-usage_count')

def tag_search_ajax(request):
    """タグ検索Ajax"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'tags': []})
    
    tags = Tag.objects.filter(
        Q(name__icontains=query) & Q(is_active=True)
    ).values('id', 'name', 'category')[:10]
    
    return JsonResponse({'tags': list(tags)})