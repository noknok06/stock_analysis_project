# ========================================
# apps/notes/views.py - 最適化版（重複削除）
# ========================================

import json
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from apps.notes.models import Notebook, Entry, SubNotebook
from apps.tags.models import Tag
from apps.notes.forms import NotebookForm, EntryForm, SubNotebookForm, NotebookSearchForm
from apps.common.mixins import UserOwnerMixin, SearchMixin
from apps.notes.services import NotebookService
from apps.common.utils import ContentHelper, TagHelper, SearchHelper
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods


# ========================================
# 共通ユーティリティ関数（重複削除）
# ========================================

def get_csrf_token_from_request(request):
    """CSRFトークンを取得"""
    return request.META.get('CSRF_COOKIE')

def create_json_response(success=True, data=None, error=None, status=200):
    """統一されたJSON レスポンス作成"""
    response_data = {'success': success}
    if data:
        response_data.update(data)
    if error:
        response_data['error'] = error
    return JsonResponse(response_data, status=status)

def handle_ajax_error(error, default_message="処理中にエラーが発生しました"):
    """Ajax エラーハンドリング"""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Ajax エラー: {error}", exc_info=True)
    return create_json_response(
        success=False, 
        error=str(error) if error else default_message, 
        status=500
    )


# ========================================
# ビュークラス
# ========================================

class NotebookListView(UserOwnerMixin, ListView):
    """ノート一覧ビュー（検索機能付き）"""
    model = Notebook
    template_name = 'notes/index.html'
    context_object_name = 'notebooks'
    paginate_by = 12
    
    def get_queryset(self):
        """検索とフィルタリングを適用したクエリセット"""
        queryset = super().get_queryset()
        
        # 検索クエリの適用
        search_query = self.get_search_query()
        if search_query:
            queryset = self.apply_search(queryset, search_query)
        
        # フィルターの適用
        queryset = self.apply_filters(queryset)
        
        # 統計情報の追加
        return queryset.annotate(
            recent_entries_count=Count(
                'entries',
                filter=Q(entries__created_at__gte=timezone.now() - timedelta(days=30))
            ),
            stock_count=Count('entries__stock_code', distinct=True)
        ).select_related().prefetch_related(
            'tags',
            Prefetch('sub_notebooks', queryset=SubNotebook.objects.order_by('order'))
        ).distinct()
    
    def get_search_query(self):
        """検索クエリを取得"""
        return self.request.GET.get('q', '').strip()
    
    def apply_search(self, queryset, search_query):
        """検索を適用"""
        search_fields = [
            'title', 'subtitle', 'description', 'investment_strategy',
            'tags__name', 'tags__description', 'entries__title', 
            'entries__company_name', 'entries__stock_code',
        ]
        
        search_terms = [term.strip() for term in search_query.split() if term.strip()]
        q_objects = Q()
        
        for term in search_terms:
            term_query = Q()
            for field in search_fields:
                term_query |= Q(**{f"{field}__icontains": term})
            q_objects &= term_query
        
        return queryset.filter(q_objects).distinct()
    
    def apply_filters(self, queryset):
        """フィルターを適用"""
        filters = {
            'notebook_type': self.request.GET.get('notebook_type'),
            'status': self.request.GET.get('status'),
            'is_favorite': self.request.GET.get('is_favorite')
        }
        
        for key, value in filters.items():
            if value:
                if key == 'is_favorite':
                    queryset = queryset.filter(is_favorite=True)
                else:
                    queryset = queryset.filter(**{key: value})
        
        # タグフィルター
        tag_ids = self.request.GET.getlist('tags')
        if tag_ids:
            queryset = queryset.filter(tags__in=tag_ids).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """コンテキストデータを追加"""
        context = super().get_context_data(**kwargs)
        
        search_query = self.get_search_query()
        context.update({
            'search_form': NotebookSearchForm(self.request.GET),
            'search_query': search_query,
            'trending_tags': Tag.objects.get_trending_tags(limit=15),
            'search_stats': self.get_search_statistics(search_query) if search_query else None,
        })
        
        return context
    
    def get_search_statistics(self, search_query):
        """検索統計情報を取得"""
        try:
            total_matches = self.get_queryset().count()
            tag_matches = Tag.objects.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query),
                notebook__user=self.request.user
            ).distinct().count()
            entry_matches = Entry.objects.filter(
                Q(title__icontains=search_query) | 
                Q(company_name__icontains=search_query) |
                Q(stock_code__icontains=search_query),
                notebook__user=self.request.user
            ).distinct().count()
            
            return {
                'total_matches': total_matches,
                'tag_matches': tag_matches,
                'entry_matches': entry_matches,
                'query': search_query
            }
        except Exception:
            return {'total_matches': 0, 'query': search_query}


class NotebookDetailView(UserOwnerMixin, DetailView):
    """ノート詳細ビュー"""
    model = Notebook
    template_name = 'notes/detail.html'
    context_object_name = 'notebook'
    
    def get_context_data(self, **kwargs):
        """エントリー一覧をページネーション付きで追加"""
        context = super().get_context_data(**kwargs)
        
        # エントリー一覧の取得とフィルタリング
        entries_list = self.get_filtered_entries()
        
        # ページネーション
        paginator = Paginator(entries_list, 10)
        page_number = self.request.GET.get('page')
        entries = paginator.get_page(page_number)
        
        context.update({
            'entries': entries,
            'is_paginated': entries.has_other_pages(),
            'page_obj': entries,
            'sub_notebooks': self.object.sub_notebooks.all(),
            'stocks': self.object.get_stocks_list(),
            'stats': self.get_notebook_stats(),
        })
        
        return context
    
    def get_filtered_entries(self):
        """フィルター済みエントリー一覧を取得"""
        entries = self.object.entries.select_related('sub_notebook').prefetch_related('tags')
        
        # フィルターの適用
        filters = {
            'sub_notebook': self.request.GET.get('sub_notebook'),
            'entry_type': self.request.GET.get('entry_type'),
            'stock_code': self.request.GET.get('stock_code'),
        }
        
        for key, value in filters.items():
            if value:
                entries = entries.filter(**{key: value})
        
        return entries.order_by('-created_at')
    
    def get_notebook_stats(self):
        """ノートブック統計情報を取得"""
        return {
            'total_entries': self.object.entry_count,
            'stock_count': self.object.get_stock_count(),
            'recent_entries': self.object.entries.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'important_entries': self.object.entries.filter(is_important=True).count(),
        }


class NotebookCreateView(LoginRequiredMixin, CreateView):
    """ノート作成ビュー"""
    model = Notebook
    form_class = NotebookForm
    template_name = 'notes/create.html'
    success_url = reverse_lazy('notes:list')
    
    def form_valid(self, form):
        """フォーム有効時の処理"""
        try:
            form.instance.user = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, f'ノート「{self.object.title}」を作成しました。')
            return redirect('notes:detail', pk=self.object.pk)
        except Exception as e:
            messages.error(self.request, f'ノートの作成に失敗しました: {str(e)}')
            return self.form_invalid(form)


class NotebookUpdateView(UserOwnerMixin, UpdateView):
    """ノート編集ビュー"""
    model = Notebook
    form_class = NotebookForm
    template_name = 'notes/edit.html'
    
    def get_success_url(self):
        return reverse_lazy('notes:detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        """編集用の追加コンテキスト"""
        context = super().get_context_data(**kwargs)
        
        # 既存タグとサブノートをJavaScript用に準備
        context.update({
            'existing_tags_json': json.dumps([
                {'id': tag.pk, 'name': tag.name, 'category': tag.category}
                for tag in self.object.tags.all()
            ]),
            'existing_sub_notebooks_json': json.dumps([
                {'title': sub.title, 'description': sub.description}
                for sub in self.object.sub_notebooks.all()
            ])
        })
        
        return context


# ========================================
# Ajax ビュー関数（統合版）
# ========================================

@login_required
def trending_tags_ajax(request):
    """トレンドタグをAjaxで取得"""
    try:
        category = request.GET.get('category', '')
        limit = int(request.GET.get('limit', 10))
        
        tags = (Tag.objects.get_tags_by_category(category, limit=limit) 
                if category else Tag.objects.get_trending_tags(limit=limit))
        
        tags_data = [{
            'id': tag.pk,
            'name': tag.name,
            'category': tag.category,
            'category_display': tag.get_category_display(),
            'description': tag.description,
            'usage_count': tag.usage_count,
            'color_class': tag.get_color_class(),
            'notebook_count': tag.notebook_set.filter(user=request.user).count(),
            'entry_count': tag.entry_set.filter(notebook__user=request.user).count(),
        } for tag in tags]
        
        return create_json_response(data={
            'tags': tags_data,
            'category': category,
            'count': len(tags_data)
        })
        
    except Exception as e:
        return handle_ajax_error(e, 'トレンドタグの取得に失敗しました')


@login_required
def tag_search_ajax(request):
    """タグ検索Ajax"""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    limit = int(request.GET.get('limit', 20))
    
    try:
        tags = (Tag.objects.search_tags(query) if query 
                else Tag.objects.get_tags_by_category(category, limit=limit) if category
                else Tag.objects.get_popular_tags(limit=limit))
        
        if category and query:
            tags = tags.filter(category=category)
        
        results = [{
            'id': tag.pk,
            'name': tag.name,
            'category': tag.category,
            'category_display': tag.get_category_display(),
            'description': tag.description,
            'usage_count': tag.usage_count,
            'color_class': tag.get_color_class(),
            'user_notebook_count': tag.notebook_set.filter(user=request.user).count(),
            'user_entry_count': tag.entry_set.filter(notebook__user=request.user).count(),
        } for tag in tags[:limit]]
        
        return create_json_response(data={
            'results': results,
            'query': query,
            'category': category,
            'count': len(results)
        })
        
    except Exception as e:
        return handle_ajax_error(e, 'タグ検索中にエラーが発生しました')


@login_required
def entry_create_view(request, notebook_pk):
    """エントリー作成ビュー"""
    notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
    
    if request.method == 'POST':
        try:
            entry_data = {
                'entry_type': request.POST.get('entry_type'),
                'title': request.POST.get('title'),
                'stock_code': request.POST.get('stock_code', ''),
                'company_name': request.POST.get('company_name', ''),
                'market': request.POST.get('market', ''),
                'content': json.loads(request.POST.get('content', '{}')),
            }
            
            # バリデーション
            if not entry_data['entry_type'] or not entry_data['title']:
                messages.error(request, 'エントリータイプとタイトルは必須です。')
                return redirect('notes:detail', pk=notebook_pk)
            
            # サブノートの処理
            sub_notebook = None
            sub_notebook_id = request.POST.get('sub_notebook')
            if sub_notebook_id:
                try:
                    sub_notebook = SubNotebook.objects.get(pk=sub_notebook_id, notebook=notebook)
                except SubNotebook.DoesNotExist:
                    pass
            
            # エントリー作成
            entry = Entry.objects.create(
                notebook=notebook,
                sub_notebook=sub_notebook,
                **entry_data
            )
            
            messages.success(request, f'エントリー「{entry_data["title"]}」を作成しました。')
            return redirect('notes:detail', pk=notebook_pk)
            
        except Exception as e:
            messages.error(request, f'エントリーの作成に失敗しました: {str(e)}')
            return redirect('notes:detail', pk=notebook_pk)
    
    return redirect('notes:detail', pk=notebook_pk)


@login_required
def entry_detail_ajax(request, entry_pk):
    """エントリー詳細をAjaxで返すビュー"""
    try:
        entry = get_object_or_404(Entry, pk=entry_pk, notebook__user=request.user)
        html_content = ContentHelper.render_entry_content_html(entry)
        
        return create_json_response(data={
            'title': entry.title,
            'entry_type': entry.get_entry_type_display(),
            'stock_info': entry.get_stock_display(),
            'sub_notebook': entry.sub_notebook.title if entry.sub_notebook else None,
            'created_at': entry.created_at.strftime('%Y/%m/%d %H:%M'),
            'is_important': entry.is_important,
            'is_bookmarked': entry.is_bookmarked,
            'html': html_content
        })
        
    except Entry.DoesNotExist:
        return create_json_response(success=False, error='エントリーが見つかりません', status=404)
    except Exception as e:
        return handle_ajax_error(e, 'エラーが発生しました')


@login_required
@require_http_methods(["POST"])
def toggle_favorite_view(request, pk):
    """ノートのお気に入り切り替え"""
    try:
        notebook = get_object_or_404(Notebook, pk=pk, user=request.user)
        notebook.is_favorite = not notebook.is_favorite
        notebook.save(update_fields=['is_favorite'])
        
        status = 'お気に入りに追加' if notebook.is_favorite else 'お気に入りから削除'
        return create_json_response(data={
            'is_favorite': notebook.is_favorite,
            'message': f'「{notebook.title}」を{status}しました'
        })
    except Exception as e:
        return handle_ajax_error(e, 'お気に入りの切り替えに失敗しました')


@login_required
@require_http_methods(["POST"])
def toggle_bookmark_view(request, entry_pk):
    """エントリーのブックマーク切り替え"""
    try:
        entry = get_object_or_404(Entry, pk=entry_pk, notebook__user=request.user)
        entry.is_bookmarked = not entry.is_bookmarked
        entry.save(update_fields=['is_bookmarked'])
        
        status = 'ブックマークに追加' if entry.is_bookmarked else 'ブックマークから削除'
        return create_json_response(data={
            'is_bookmarked': entry.is_bookmarked,
            'message': f'「{entry.title}」を{status}しました'
        })
    except Exception as e:
        return handle_ajax_error(e, 'ブックマークの切り替えに失敗しました')


@login_required
@require_http_methods(["POST"])
def sub_notebook_create_ajax(request, notebook_pk):
    """サブノート作成Ajax"""
    try:
        notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
        data = json.loads(request.body)
        
        title = data.get('title', '').strip()
        if not title:
            return create_json_response(
                success=False, 
                error='サブノート名は必須です', 
                status=400
            )
        
        # 重複チェック
        if SubNotebook.objects.filter(notebook=notebook, title=title).exists():
            return create_json_response(
                success=False, 
                error='同名のサブノートが既に存在します', 
                status=400
            )
        
        # サブノート作成
        sub_notebook = SubNotebook.objects.create(
            notebook=notebook,
            title=title,
            description=data.get('description', '').strip(),
            order=notebook.sub_notebooks.count()
        )
        
        return create_json_response(data={
            'sub_notebook': {
                'id': str(sub_notebook.pk),
                'title': sub_notebook.title,
                'description': sub_notebook.description
            },
            'message': f'サブノート「{title}」を作成しました'
        })
        
    except json.JSONDecodeError:
        return create_json_response(
            success=False, 
            error='無効なJSONデータです', 
            status=400
        )
    except Exception as e:
        return handle_ajax_error(e, 'サブノートの作成に失敗しました')


# ========================================
# 検索ビュー（統合版）
# ========================================

class NotebookSearchResultsView(UserOwnerMixin, ListView):
    """詳細検索結果ページ"""
    model = Notebook
    template_name = 'notes/search_results.html'
    context_object_name = 'notebooks'
    paginate_by = 20
    
    def get_queryset(self):
        """高度な検索クエリを構築"""
        queryset = super().get_queryset()
        
        # 基本検索
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = self.apply_comprehensive_search(queryset, search_query)
        
        # 詳細フィルターの適用
        return self.apply_advanced_filters(queryset)
    
    def apply_comprehensive_search(self, queryset, search_query):
        """包括的な検索を適用"""
        search_terms = [term.strip() for term in search_query.split() if term.strip()]
        if not search_terms:
            return queryset
        
        search_fields = [
            'title', 'subtitle', 'description', 'investment_strategy',
            'tags__name', 'tags__description', 'entries__title',
            'entries__company_name', 'entries__stock_code',
        ]
        
        for term in search_terms:
            term_query = Q()
            for field in search_fields:
                term_query |= Q(**{f"{field}__icontains": term})
            queryset = queryset.filter(term_query)
        
        return queryset.distinct()
    
    def apply_advanced_filters(self, queryset):
        """詳細フィルターを適用"""
        filters = {
            'date_from': self.request.GET.get('date_from'),
            'date_to': self.request.GET.get('date_to'),
            'min_entries': self.request.GET.get('min_entries'),
            'max_entries': self.request.GET.get('max_entries'),
            'has_tags': self.request.GET.get('has_tags'),
        }
        
        # 日付範囲フィルター
        if filters['date_from']:
            try:
                date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__gte=date_from)
            except ValueError:
                pass
        
        if filters['date_to']:
            try:
                date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__lte=date_to)
            except ValueError:
                pass
        
        # エントリー数フィルター
        if filters['min_entries']:
            try:
                queryset = queryset.filter(entry_count__gte=int(filters['min_entries']))
            except ValueError:
                pass
        
        if filters['max_entries']:
            try:
                queryset = queryset.filter(entry_count__lte=int(filters['max_entries']))
            except ValueError:
                pass
        
        # タグ有無フィルター
        if filters['has_tags'] == 'true':
            queryset = queryset.filter(tags__isnull=False).distinct()
        elif filters['has_tags'] == 'false':
            queryset = queryset.filter(tags__isnull=True)
        
        return queryset.select_related().prefetch_related('tags').distinct()