# ========================================
# apps/tags/views.py - 改良版タグ管理ビュー
# ========================================

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import ListView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin  
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from apps.tags.models import Tag
from apps.notes.models import Notebook, Entry


class TagListView(ListView):
    """改良されたタグ一覧ビュー"""
    model = Tag
    template_name = 'tags/list.html'
    context_object_name = 'tags'
    paginate_by = 50
    
    def get_queryset(self):
        """検索・フィルター付きクエリセット"""
        queryset = Tag.objects.all()
        
        # 検索クエリ
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # カテゴリフィルター
        category = self.request.GET.get('category', '')
        if category:
            queryset = queryset.filter(category=category)
        
        # アクティブ状態フィルター
        is_active = self.request.GET.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        # 使用状況フィルター
        usage_filter = self.request.GET.get('usage', '')
        if usage_filter == 'used':
            queryset = queryset.filter(usage_count__gt=0)
        elif usage_filter == 'unused':
            queryset = queryset.filter(usage_count=0)
        
        # ソート
        sort_by = self.request.GET.get('sort', '-usage_count')
        valid_sorts = ['-usage_count', 'usage_count', 'name', '-name', 
                      '-created_at', 'created_at', '-updated_at', 'updated_at']
        if sort_by in valid_sorts:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-usage_count', 'name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """コンテキストデータを追加"""
        context = super().get_context_data(**kwargs)
        
        # 統計情報
        all_tags = Tag.objects.all()
        context['stats'] = {
            'total_tags': all_tags.count(),
            'active_tags': all_tags.filter(is_active=True).count(),
            'used_tags': all_tags.filter(usage_count__gt=0).count(),
            'total_usage': all_tags.aggregate(total=Sum('usage_count'))['total'] or 0,
        }
        
        # カテゴリ別統計
        context['category_stats'] = []
        for category, display_name in Tag.CATEGORY_CHOICES:
            count = all_tags.filter(category=category).count()
            used_count = all_tags.filter(category=category, usage_count__gt=0).count()
            context['category_stats'].append({
                'category': category,
                'display_name': display_name,
                'count': count,
                'used_count': used_count,
                'usage_percentage': round((used_count / count * 100) if count > 0 else 0, 1)
            })
        
        # 検索・フィルター情報
        context['current_filters'] = {
            'q': self.request.GET.get('q', ''),
            'category': self.request.GET.get('category', ''),
            'is_active': self.request.GET.get('is_active', ''),
            'usage': self.request.GET.get('usage', ''),
            'sort': self.request.GET.get('sort', '-usage_count'),
        }
        
        # 最近作成されたタグ
        recent_threshold = timezone.now() - timedelta(days=7)
        context['recent_tags'] = Tag.objects.filter(
            created_at__gte=recent_threshold
        ).order_by('-created_at')[:5]
        
        # トレンドタグ（最近使用されたタグ）
        context['trending_tags'] = Tag.objects.get_trending_tags(limit=10)
        
        return context


class TagUpdateView(LoginRequiredMixin, UpdateView):
    """タグ編集ビュー"""
    model = Tag
    fields = ['name', 'category', 'description', 'color', 'is_active']
    template_name = 'tags/edit.html'
    success_url = reverse_lazy('tags:list')
    
    def form_valid(self, form):
        """フォーム有効時の処理"""
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'タグ「{self.object.name}」を更新しました。')
            return response
        except Exception as e:
            messages.error(self.request, f'タグの更新に失敗しました: {str(e)}')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """コンテキストデータを追加"""
        context = super().get_context_data(**kwargs)
        
        # タグの使用統計
        tag = self.object
        context['usage_stats'] = {
            'notebooks': tag.notebook_set.count(),
            'entries': tag.entry_set.count(),
            'total_usage': tag.usage_count,
        }
        
        # 関連ノートブック（最新5件）
        context['related_notebooks'] = tag.notebook_set.select_related('user').order_by('-updated_at')[:5]
        
        # 関連エントリー（最新5件）
        context['related_entries'] = tag.entry_set.select_related('notebook').order_by('-created_at')[:5]
        
        return context


class TagDeleteView(LoginRequiredMixin, DeleteView):
    """タグ削除ビュー"""
    model = Tag
    template_name = 'tags/delete.html'
    success_url = reverse_lazy('tags:list')
    
    def delete(self, request, *args, **kwargs):
        """削除処理"""
        tag = self.get_object()
        tag_name = tag.name
        
        # 使用中のタグの場合は警告
        if tag.usage_count > 0:
            messages.warning(
                request, 
                f'タグ「{tag_name}」は{tag.usage_count}回使用されていますが、削除しました。'
            )
        else:
            messages.success(request, f'タグ「{tag_name}」を削除しました。')
        
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """削除確認用のコンテキスト"""
        context = super().get_context_data(**kwargs)
        
        tag = self.object
        context['usage_stats'] = {
            'notebooks': tag.notebook_set.count(),
            'entries': tag.entry_set.count(),
            'total_usage': tag.usage_count,
        }
        
        return context


@login_required
@require_http_methods(["POST"])
def tag_quick_edit_ajax(request, tag_id):
    """タグのクイック編集Ajax"""
    try:
        tag = get_object_or_404(Tag, pk=tag_id)
        data = json.loads(request.body)
        
        # 更新可能なフィールドを制限
        allowed_fields = ['name', 'description', 'category', 'is_active', 'color']
        
        for field, value in data.items():
            if field in allowed_fields:
                setattr(tag, field, value)
        
        tag.save()
        
        return JsonResponse({
            'success': True,
            'message': f'タグ「{tag.name}」を更新しました',
            'tag': {
                'id': tag.pk,
                'name': tag.name,
                'category': tag.category,
                'category_display': tag.get_category_display(),
                'description': tag.description,
                'usage_count': tag.usage_count,
                'is_active': tag.is_active,
                'color': tag.color,
                'color_class': tag.get_color_class(),
            }
        })
        
    except Tag.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'タグが見つかりません'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無効なJSONデータです'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def tag_toggle_status_ajax(request, tag_id):
    """タグのアクティブ状態切り替えAjax"""
    try:
        tag = get_object_or_404(Tag, pk=tag_id)
        tag.is_active = not tag.is_active
        tag.save(update_fields=['is_active'])
        
        status = 'アクティブ' if tag.is_active else '無効'
        return JsonResponse({
            'success': True,
            'is_active': tag.is_active,
            'message': f'タグ「{tag.name}」を{status}にしました'
        })
        
    except Tag.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'タグが見つかりません'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def tag_bulk_action_ajax(request):
    """タグの一括操作Ajax"""
    try:
        data = json.loads(request.body)
        action = data.get('action')
        tag_ids = data.get('tag_ids', [])
        
        if not tag_ids:
            return JsonResponse({
                'success': False,
                'error': 'タグが選択されていません'
            }, status=400)
        
        tags = Tag.objects.filter(pk__in=tag_ids)
        count = tags.count()
        
        if action == 'activate':
            tags.update(is_active=True)
            message = f'{count}個のタグをアクティブにしました'
        elif action == 'deactivate':
            tags.update(is_active=False)
            message = f'{count}個のタグを無効にしました'
        elif action == 'delete':
            tags.delete()
            message = f'{count}個のタグを削除しました'
        else:
            return JsonResponse({
                'success': False,
                'error': '無効なアクションです'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': message,
            'affected_count': count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無効なJSONデータです'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def tag_search_ajax(request):
    """タグ検索Ajax（リアルタイム検索用）"""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    limit = int(request.GET.get('limit', 20))
    
    try:
        tags = Tag.objects.all()
        
        if query:
            tags = tags.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query)
            )
        
        if category:
            tags = tags.filter(category=category)
        
        tags = tags.order_by('-usage_count', 'name')[:limit]
        
        results = []
        for tag in tags:
            results.append({
                'id': tag.pk,
                'name': tag.name,
                'category': tag.category,
                'category_display': tag.get_category_display(),
                'description': tag.description,
                'usage_count': tag.usage_count,
                'is_active': tag.is_active,
                'color_class': tag.get_color_class(),
                'edit_url': f'/tags/{tag.pk}/edit/',
                'delete_url': f'/tags/{tag.pk}/delete/',
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results),
            'query': query
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def tag_usage_stats_ajax(request, tag_id):
    """タグ使用統計Ajax"""
    try:
        tag = get_object_or_404(Tag, pk=tag_id)
        
        # 関連ノートブック
        notebooks = tag.notebook_set.select_related('user')
        notebook_data = [
            {
                'id': str(nb.pk),
                'title': nb.title,
                'user': nb.user.username,
                'updated_at': nb.updated_at.isoformat(),
                'url': f'/notes/{nb.pk}/'
            }
            for nb in notebooks[:10]
        ]
        
        # 関連エントリー
        entries = tag.entry_set.select_related('notebook')
        entry_data = [
            {
                'id': str(entry.pk),
                'title': entry.title,
                'notebook_title': entry.notebook.title,
                'created_at': entry.created_at.isoformat(),
                'url': f'/notes/{entry.notebook.pk}/#entry-{entry.pk}'
            }
            for entry in entries[:10]
        ]
        
        return JsonResponse({
            'success': True,
            'tag': {
                'id': tag.pk,
                'name': tag.name,
                'usage_count': tag.usage_count,
                'created_at': tag.created_at.isoformat(),
            },
            'notebooks': {
                'count': notebooks.count(),
                'data': notebook_data
            },
            'entries': {
                'count': entries.count(),
                'data': entry_data
            }
        })
        
    except Tag.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'タグが見つかりません'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def tag_search_ajax_legacy(request):
    """レガシータグ検索Ajax（既存コードとの互換性用）"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'tags': []})
    
    tags = Tag.objects.filter(
        Q(name__icontains=query) & Q(is_active=True)
    ).values('id', 'name', 'category')[:10]
    
    return JsonResponse({'tags': list(tags)})