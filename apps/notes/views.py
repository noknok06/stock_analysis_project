# ========================================
# apps/notes/views.py - 見直し版（テーマ単位ノート対応）
# ========================================

import json
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
from apps.notes.models import Notebook, Entry, SubNotebook, NotebookTemplate, Tag
from apps.notes.forms import NotebookForm, EntryForm, SubNotebookForm, NotebookSearchForm
from apps.common.mixins import UserOwnerMixin, SearchMixin
from apps.notes.services import NotebookService
from apps.common.utils import ContentHelper, TagHelper
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


class NotebookListView(UserOwnerMixin, SearchMixin, ListView):
    """ノート一覧ビュー（トレンドタグ機能追加）"""
    model = Notebook
    template_name = 'notes/index.html'
    context_object_name = 'notebooks'
    paginate_by = 12
    search_fields = ['title', 'subtitle', 'description', 'investment_strategy']
    
    def get_queryset(self):
        """検索とフィルタリングを適用したクエリセット"""
        queryset = super().get_queryset()
        queryset = self.apply_search(queryset)
        
        # ノートタイプフィルター
        notebook_type = self.request.GET.get('notebook_type')
        if notebook_type:
            queryset = queryset.filter(notebook_type=notebook_type)
        
        # ステータスフィルター
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # お気に入りフィルター
        is_favorite = self.request.GET.get('is_favorite')
        if is_favorite:
            queryset = queryset.filter(is_favorite=True)
        
        # タグフィルター
        tag_ids = self.request.GET.getlist('tags')
        if tag_ids:
            queryset = queryset.filter(tags__in=tag_ids).distinct()
        
        # 統計情報も取得
        queryset = queryset.annotate(
            recent_entries_count=Count(
                'entries',
                filter=Q(entries__created_at__gte=timezone.now() - timedelta(days=30))
            ),
            stock_count=Count('entries__stock_code', distinct=True)
        )
        
        return queryset.select_related().prefetch_related(
            'tags',
            Prefetch('sub_notebooks', queryset=SubNotebook.objects.order_by('order'))
        )
    
    def get_context_data(self, **kwargs):
        """コンテキストデータを追加（トレンドタグ追加）"""
        context = super().get_context_data(**kwargs)
        context['search_form'] = NotebookSearchForm(self.request.GET)
        context['search_query'] = self.get_search_query()
        
        # ★ トレンドタグを追加
        context['trending_tags'] = Tag.objects.get_trending_tags(limit=15)
        
        # カテゴリ別タグ
        context['popular_strategy_tags'] = Tag.objects.get_tags_by_category('STRATEGY', limit=8)
        context['popular_stock_tags'] = Tag.objects.get_tags_by_category('STOCK', limit=8)
        context['popular_sector_tags'] = Tag.objects.get_tags_by_category('SECTOR', limit=8)
        
        # お気に入りノートの表示
        context['favorite_notebooks'] = self.model.objects.filter(
            user=self.request.user, 
            is_favorite=True
        )[:5]
        
        # 最近更新されたノート
        context['recent_notebooks'] = self.model.objects.filter(
            user=self.request.user
        ).order_by('-updated_at')[:5]
        
        return context


# ========================================
# トレンドタグ専用Ajax View
# ========================================

@login_required
def trending_tags_ajax(request):
    """トレンドタグをAjaxで取得"""
    try:
        category = request.GET.get('category', '')
        limit = int(request.GET.get('limit', 10))
        
        if category:
            tags = Tag.objects.get_tags_by_category(category, limit=limit)
        else:
            tags = Tag.objects.get_trending_tags(limit=limit)
        
        # タグデータをシリアライズ
        tags_data = []
        for tag in tags:
            # そのタグを使用しているノートブック数を取得
            notebook_count = tag.notebook_set.filter(user=request.user).count()
            entry_count = tag.entry_set.filter(notebook__user=request.user).count()
            
            tags_data.append({
                'id': tag.pk,
                'name': tag.name,
                'category': tag.category,
                'category_display': tag.get_category_display(),
                'description': tag.description,
                'usage_count': tag.usage_count,
                'color_class': tag.get_color_class(),
                'notebook_count': notebook_count,
                'entry_count': entry_count,
                'search_url': f"{reverse('notes:list')}?q={tag.name}"
            })
        
        return JsonResponse({
            'success': True,
            'tags': tags_data,
            'category': category,
            'count': len(tags_data)
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"トレンドタグ取得エラー: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'トレンドタグの取得に失敗しました'
        }, status=500)


@login_required
def tag_search_ajax(request):
    """タグ検索Ajax"""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    limit = int(request.GET.get('limit', 20))
    
    try:
        if query:
            # テキスト検索
            tags = Tag.objects.search_tags(query)
            if category:
                tags = tags.filter(category=category)
            tags = tags[:limit]
        else:
            # カテゴリ別取得
            if category:
                tags = Tag.objects.get_tags_by_category(category, limit=limit)
            else:
                tags = Tag.objects.get_popular_tags(limit=limit)
        
        # 結果をシリアライズ
        results = []
        for tag in tags:
            # ユーザーの関連ノートブック・エントリー数
            user_notebook_count = tag.notebook_set.filter(user=request.user).count()
            user_entry_count = tag.entry_set.filter(notebook__user=request.user).count()
            
            results.append({
                'id': tag.pk,
                'name': tag.name,
                'category': tag.category,
                'category_display': tag.get_category_display(),
                'description': tag.description,
                'usage_count': tag.usage_count,
                'color_class': tag.get_color_class(),
                'user_notebook_count': user_notebook_count,
                'user_entry_count': user_entry_count,
                'total_related': user_notebook_count + user_entry_count
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'query': query,
            'category': category,
            'count': len(results)
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"タグ検索エラー: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'タグ検索中にエラーが発生しました'
        }, status=500)



class NotebookDetailView(UserOwnerMixin, DetailView):
    """ノート詳細ビュー（テーマ単位）"""
    model = Notebook
    template_name = 'notes/detail.html'
    context_object_name = 'notebook'
    
    def get_context_data(self, **kwargs):
        """エントリー一覧をページネーション付きで追加"""
        context = super().get_context_data(**kwargs)
        
        # エントリー一覧をページネーションで取得
        entries_list = self.object.entries.select_related('sub_notebook').prefetch_related('tags').order_by('-created_at')
        
        # サブノートフィルター
        sub_notebook_id = self.request.GET.get('sub_notebook')
        if sub_notebook_id:
            entries_list = entries_list.filter(sub_notebook_id=sub_notebook_id)
        
        # エントリータイプフィルター
        entry_type = self.request.GET.get('entry_type')
        if entry_type:
            entries_list = entries_list.filter(entry_type=entry_type)
        
        # 銘柄フィルター
        stock_code = self.request.GET.get('stock_code')
        if stock_code:
            entries_list = entries_list.filter(stock_code=stock_code)
        
        # ページネーション
        paginator = Paginator(entries_list, 10)  # 1ページ10エントリー
        page_number = self.request.GET.get('page')
        entries = paginator.get_page(page_number)
        
        context['entries'] = entries
        context['is_paginated'] = entries.has_other_pages()
        context['page_obj'] = entries
        
        # サブノート一覧
        context['sub_notebooks'] = self.object.sub_notebooks.all()
        
        # 銘柄一覧（フィルター用）
        context['stocks'] = self.object.get_stocks_list()
        
        # 統計情報
        context['stats'] = {
            'total_entries': self.object.entry_count,
            'stock_count': self.object.get_stock_count(),
            'recent_entries': self.object.entries.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'important_entries': self.object.entries.filter(is_important=True).count(),
        }
        
        return context


class NotebookCreateView(LoginRequiredMixin, CreateView):
    """ノート作成ビュー（テーマ単位）"""
    model = Notebook
    form_class = NotebookForm
    template_name = 'notes/create.html'
    success_url = reverse_lazy('notes:list')
    
    def get_context_data(self, **kwargs):
        """テンプレート情報を追加"""
        context = super().get_context_data(**kwargs)
        context['templates'] = NotebookTemplate.objects.filter(is_active=True)
        return context
    
    def form_valid(self, form):
        """フォーム有効時の処理"""
        try:
            form.instance.user = self.request.user
            
            # テンプレートが選択されている場合、テンプレートの設定を適用
            template = form.cleaned_data.get('template')
            if template:
                if not form.instance.title:
                    form.instance.title = template.default_title
                if not form.instance.investment_strategy:
                    form.instance.investment_strategy = template.default_strategy
                if not form.instance.key_criteria:
                    form.instance.key_criteria = template.default_criteria
            
            response = super().form_valid(form)
            
            # テンプレートの推奨サブノートを作成
            if template and template.suggested_sub_notebooks:
                for order, sub_notebook_name in enumerate(template.suggested_sub_notebooks):
                    SubNotebook.objects.create(
                        notebook=self.object,
                        title=sub_notebook_name,
                        order=order
                    )
            
            messages.success(self.request, f'ノート「{self.object.title}」を作成しました。')
            
            # 成功時はノート詳細ページにリダイレクト
            return redirect('notes:detail', pk=self.object.pk)
        except Exception as e:
            messages.error(self.request, f'ノートの作成に失敗しました: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """フォーム無効時の処理"""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{form[field].label}: {error}')
        return super().form_invalid(form)


class NotebookUpdateView(UserOwnerMixin, UpdateView):
    """ノート編集ビュー（テーマ単位）"""
    model = Notebook
    form_class = NotebookForm
    template_name = 'notes/edit.html'
    
    def get_success_url(self):
        return reverse_lazy('notes:detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        """編集用の追加コンテキスト"""
        context = super().get_context_data(**kwargs)
        
        # 既存タグをJavaScript用に準備
        existing_tags = [
            {'id': tag.pk, 'name': tag.name, 'category': tag.category}
            for tag in self.object.tags.all()
        ]
        context['existing_tags_json'] = json.dumps(existing_tags)
        
        # 既存サブノートを準備
        existing_sub_notebooks = [
            {'title': sub.title, 'description': sub.description}
            for sub in self.object.sub_notebooks.all()
        ]
        context['existing_sub_notebooks_json'] = json.dumps(existing_sub_notebooks)
        
        return context
    
    def form_valid(self, form):
        """フォーム有効時の処理"""
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'ノート「{self.object.title}」を更新しました。')
            return response
        except Exception as e:
            messages.error(self.request, f'ノートの更新に失敗しました: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """フォーム無効時の処理"""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{form[field].label}: {error}')
        return super().form_invalid(form)


# ========================================
# エントリー関連ビュー
# ========================================

@login_required
def entry_create_view(request, notebook_pk):
    """エントリー作成ビュー（銘柄情報付き）"""
    notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
    
    if request.method == 'POST':
        try:
            # フォームデータを処理
            entry_type = request.POST.get('entry_type')
            title = request.POST.get('title')
            stock_code = request.POST.get('stock_code', '')
            company_name = request.POST.get('company_name', '')
            market = request.POST.get('market', '')
            sub_notebook_id = request.POST.get('sub_notebook')
            content_json = request.POST.get('content', '{}')
            
            if not entry_type or not title:
                messages.error(request, 'エントリータイプとタイトルは必須です。')
                return redirect('notes:detail', pk=notebook_pk)
            
            # コンテンツをパースして整形
            try:
                content_data = json.loads(content_json)
            except json.JSONDecodeError:
                content_data = {}
            
            # エントリータイプに応じてコンテンツを整形
            formatted_content = ContentHelper.format_json_content(content_data, entry_type)
            
            # サブノートの取得
            sub_notebook = None
            if sub_notebook_id:
                try:
                    sub_notebook = SubNotebook.objects.get(pk=sub_notebook_id, notebook=notebook)
                except SubNotebook.DoesNotExist:
                    pass
            
            # エントリーを作成
            entry = Entry.objects.create(
                notebook=notebook,
                sub_notebook=sub_notebook,
                entry_type=entry_type,
                title=title,
                stock_code=stock_code,
                company_name=company_name,
                market=market,
                content=formatted_content
            )
            
            # タグの自動推奨
            suggested_tags = TagHelper.suggest_tags(
                json.dumps(formatted_content), 
                notebook.tags.all()
            )
            
            messages.success(request, f'エントリー「{title}」を作成しました。')
            
            # 成功時は作成したエントリーが見えるページにリダイレクト
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
        
        # エントリータイプに応じてHTMLを生成
        html_content = render_entry_content_html(entry)
        
        return JsonResponse({
            'success': True,
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
        return JsonResponse({
            'success': False,
            'error': 'エントリーが見つかりません'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'エラーが発生しました: {str(e)}'
        }, status=500)


@login_required
def toggle_favorite_view(request, notebook_pk):
    """ノートのお気に入り切り替え"""
    if request.method == 'POST':
        notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
        notebook.is_favorite = not notebook.is_favorite
        notebook.save(update_fields=['is_favorite'])
        
        status = 'お気に入りに追加' if notebook.is_favorite else 'お気に入りから削除'
        return JsonResponse({
            'success': True,
            'is_favorite': notebook.is_favorite,
            'message': f'「{notebook.title}」を{status}しました'
        })
    
    return JsonResponse({'success': False, 'error': '無効なリクエストです'}, status=400)


@login_required
def toggle_bookmark_view(request, entry_pk):
    """エントリーのブックマーク切り替え"""
    if request.method == 'POST':
        entry = get_object_or_404(Entry, pk=entry_pk, notebook__user=request.user)
        entry.is_bookmarked = not entry.is_bookmarked
        entry.save(update_fields=['is_bookmarked'])
        
        status = 'ブックマークに追加' if entry.is_bookmarked else 'ブックマークから削除'
        return JsonResponse({
            'success': True,
            'is_bookmarked': entry.is_bookmarked,
            'message': f'「{entry.title}」を{status}しました'
        })
    
    return JsonResponse({'success': False, 'error': '無効なリクエストです'}, status=400)


@login_required
def sub_notebook_create_ajax(request, notebook_pk):
    """サブノート作成Ajax"""
    if request.method == 'POST':
        try:
            notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
            data = json.loads(request.body)
            
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            
            if not title:
                return JsonResponse({
                    'success': False,
                    'error': 'サブノート名は必須です'
                }, status=400)
            
            # 重複チェック
            if SubNotebook.objects.filter(notebook=notebook, title=title).exists():
                return JsonResponse({
                    'success': False,
                    'error': '同名のサブノートが既に存在します'
                }, status=400)
            
            # サブノート作成
            sub_notebook = SubNotebook.objects.create(
                notebook=notebook,
                title=title,
                description=description,
                order=notebook.sub_notebooks.count()
            )
            
            return JsonResponse({
                'success': True,
                'sub_notebook': {
                    'id': str(sub_notebook.pk),
                    'title': sub_notebook.title,
                    'description': sub_notebook.description
                },
                'message': f'サブノート「{title}」を作成しました'
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
    
    return JsonResponse({'success': False, 'error': '無効なリクエストです'}, status=405)


@login_required
def get_template_ajax(request, template_pk):
    """テンプレート情報をAjaxで取得"""
    try:
        template = get_object_or_404(NotebookTemplate, pk=template_pk, is_active=True)
        
        return JsonResponse({
            'success': True,
            'template': {
                'name': template.name,
                'description': template.description,
                'default_title': template.default_title,
                'default_strategy': template.default_strategy,
                'default_criteria': template.default_criteria,
                'suggested_sub_notebooks': template.suggested_sub_notebooks,
                'suggested_tags': template.suggested_tags
            }
        })
        
    except NotebookTemplate.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'テンプレートが見つかりません'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ========================================
# ヘルパー関数（既存のものを流用）
# ========================================

def render_entry_content_html(entry):
    """エントリータイプに応じたHTMLコンテンツを生成"""
    content = entry.content
    entry_type = entry.entry_type
    
    # 銘柄情報を追加
    stock_info_html = ''
    if entry.stock_code or entry.company_name:
        stock_info_html = f'''
        <div class="bg-gray-700 p-4 rounded-lg mb-4">
            <h4 class="font-semibold text-white mb-2">銘柄情報</h4>
            <div class="grid grid-cols-2 gap-4">
                {f'<div><p class="text-sm text-gray-400">銘柄コード</p><p class="text-white">{entry.stock_code}</p></div>' if entry.stock_code else ''}
                {f'<div><p class="text-sm text-gray-400">企業名</p><p class="text-white">{entry.company_name}</p></div>' if entry.company_name else ''}
                {f'<div><p class="text-sm text-gray-400">市場</p><p class="text-white">{entry.market}</p></div>' if entry.market else ''}
                {f'<div><p class="text-sm text-gray-400">イベント日</p><p class="text-white">{entry.event_date.strftime("%Y/%m/%d")}</p></div>' if entry.event_date else ''}
            </div>
        </div>
        '''
    
    # 既存のコンテンツ生成関数を使用
    if entry_type == 'ANALYSIS':
        content_html = render_analysis_content(content)
    elif entry_type == 'NEWS':
        content_html = render_news_content(content)
    elif entry_type == 'CALCULATION':
        content_html = render_calculation_content(content)
    elif entry_type == 'MEMO':
        content_html = render_memo_content(content)
    elif entry_type == 'GOAL':
        content_html = render_goal_content(content)
    else:
        content_html = '<p class="text-gray-300">コンテンツが見つかりません。</p>'
    
    return stock_info_html + content_html


# 既存のコンテンツ生成関数をそのまま使用
def render_analysis_content(content):
    """決算分析コンテンツのHTML生成（既存のまま）"""
    html = '<div class="space-y-6">'
    
    # サマリー
    if content.get('summary'):
        html += f'''
        <div class="bg-gray-700 p-4 rounded-lg">
            <h4 class="font-semibold text-white mb-2">サマリー</h4>
            <p class="text-gray-300">{content["summary"]}</p>
        </div>
        '''
    
    # 主要指標
    key_metrics = content.get('key_metrics', {})
    if any(key_metrics.values()):
        html += '<div class="grid grid-cols-2 md:grid-cols-4 gap-4">'
        for key, value in key_metrics.items():
            if value:
                display_key = {
                    'revenue': '売上高',
                    'operating_profit': '営業利益', 
                    'net_income': '純利益',
                    'eps': 'EPS'
                }.get(key, key)
                html += f'''
                <div class="bg-gray-700 p-3 rounded-lg text-center">
                    <p class="text-sm text-gray-400">{display_key}</p>
                    <p class="text-lg font-bold text-white">{value}</p>
                </div>
                '''
        html += '</div>'
    
    # 分析
    if content.get('analysis'):
        html += f'''
        <div>
            <h4 class="font-semibold text-white mb-2">分析</h4>
            <p class="text-gray-300">{content["analysis"]}</p>
        </div>
        '''
    
    # 今後の見通し
    if content.get('outlook'):
        html += f'''
        <div>
            <h4 class="font-semibold text-white mb-2">今後の見通し</h4>
            <p class="text-gray-300">{content["outlook"]}</p>
        </div>
        '''
    
    html += '</div>'
    return html


def render_news_content(content):
    """ニュースコンテンツのHTML生成（既存のまま）"""
    html = '<div class="space-y-4">'
    
    # ヘッドライン
    if content.get('headline'):
        html += f'''
        <div class="bg-gray-700 p-4 rounded-lg">
            <h4 class="font-semibold text-white mb-2">{content["headline"]}</h4>
            {f'<p class="text-gray-300">{content["content"]}</p>' if content.get("content") else ""}
        </div>
        '''
    
    # 事業への影響
    if content.get('impact'):
        html += f'''
        <div>
            <h4 class="font-semibold text-white mb-2">事業への影響</h4>
            <p class="text-gray-300">{content["impact"]}</p>
        </div>
        '''
    
    # 株価への影響
    if content.get('stock_impact'):
        html += f'''
        <div>
            <h4 class="font-semibold text-white mb-2">株価への影響</h4>
            <p class="text-gray-300">{content["stock_impact"]}</p>
        </div>
        '''
    
    html += '</div>'
    return html


def render_calculation_content(content):
    """計算結果コンテンツのHTML生成（既存のまま）"""
    html = '<div class="space-y-6">'
    
    # 現在株価
    if content.get('current_price'):
        html += f'''
        <div class="text-center bg-gray-700 p-4 rounded-lg">
            <h4 class="font-semibold text-white mb-2">現在株価</h4>
            <p class="text-3xl font-bold text-blue-400">{content["current_price"]}</p>
        </div>
        '''
    
    # 計算結果
    calculations = content.get('calculations', {})
    if any(calculations.values()):
        html += '<div class="grid grid-cols-1 md:grid-cols-2 gap-4">'
        for key, value in calculations.items():
            if value:
                display_key = {
                    'per': 'PER',
                    'pbr': 'PBR',
                    'dividend_yield': '配当利回り',
                    'roe': 'ROE',
                    'roa': 'ROA'
                }.get(key, key.upper())
                html += f'''
                <div class="bg-gray-700 p-3 rounded-lg">
                    <p class="text-sm text-gray-400">{display_key}</p>
                    <p class="text-lg font-semibold text-white">{value}</p>
                </div>
                '''
        html += '</div>'
    
    # 適正価格
    if content.get('fair_value'):
        html += f'''
        <div class="space-y-2">
            <h4 class="font-semibold text-white">適正価格</h4>
            <p class="text-xl font-bold text-green-400">{content["fair_value"]}</p>
        </div>
        '''
    
    # 推奨
    if content.get('recommendation'):
        html += f'''
        <div class="bg-blue-900/30 p-4 rounded-lg border border-blue-700">
            <h4 class="font-semibold text-white mb-2">推奨</h4>
            <p class="text-gray-300">{content["recommendation"]}</p>
        </div>
        '''
    
    html += '</div>'
    return html


def render_memo_content(content):
    """メモコンテンツのHTML生成（既存のまま）"""
    html = '<div class="space-y-4">'
    
    # 観察事項
    if content.get('observation'):
        html += f'''
        <div>
            <h4 class="font-semibold text-white mb-2">観察事項</h4>
            <p class="text-gray-300">{content["observation"]}</p>
        </div>
        '''
    
    # 市場トレンド
    if content.get('market_trend'):
        html += f'''
        <div>
            <h4 class="font-semibold text-white mb-2">市場トレンド</h4>
            <p class="text-gray-300">{content["market_trend"]}</p>
        </div>
        '''
    
    # 個人的メモ
    if content.get('personal_note'):
        html += f'''
        <div>
            <h4 class="font-semibold text-white mb-2">個人的メモ</h4>
            <p class="text-gray-300">{content["personal_note"]}</p>
        </div>
        '''
    
    # 次のアクション
    if content.get('next_action'):
        html += f'''
        <div class="bg-yellow-900/30 p-4 rounded-lg border border-yellow-700">
            <h4 class="font-semibold text-white mb-2">次のアクション</h4>
            <p class="text-gray-300">{content["next_action"]}</p>
        </div>
        '''
    
    html += '</div>'
    return html


def render_goal_content(content):
    """投資目標コンテンツのHTML生成（既存のまま）"""
    html = '<div class="space-y-6">'
    
    # 目標情報
    if content.get('target_price') or content.get('sell_timing'):
        html += '<div class="grid grid-cols-1 md:grid-cols-2 gap-4">'
        if content.get('target_price'):
            html += f'''
            <div class="space-y-2">
                <h4 class="font-semibold text-white">目標株価</h4>
                <p class="text-2xl font-bold text-green-400">{content["target_price"]}</p>
            </div>
            '''
        if content.get('sell_timing'):
            html += f'''
            <div class="space-y-2">
                <h4 class="font-semibold text-white">売却タイミング</h4>
                <p class="text-gray-300">{content["sell_timing"]}</p>
            </div>
            '''
        html += '</div>'
    
    # 投資理由
    if content.get('investment_reason'):
        html += f'''
        <div class="space-y-2">
            <h4 class="font-semibold text-white">投資理由</h4>
            <p class="text-gray-300">{content["investment_reason"]}</p>
        </div>
        '''
    
    # 期待される効果
    if content.get('expected_effect'):
        html += f'''
        <div class="bg-purple-900/30 p-4 rounded-lg border border-purple-700">
            <h4 class="font-semibold text-white mb-2">期待される効果</h4>
            <p class="text-gray-300">{content["expected_effect"]}</p>
        </div>
        '''
    
    html += '</div>'
    return html

@login_required
def toggle_favorite_view(request, pk):
    """ノートのお気に入り切り替え"""
    if request.method == 'POST':
        try:
            notebook = get_object_or_404(Notebook, pk=pk, user=request.user)
            notebook.is_favorite = not notebook.is_favorite
            notebook.save(update_fields=['is_favorite'])
            
            status = 'お気に入りに追加' if notebook.is_favorite else 'お気に入りから削除'
            return JsonResponse({
                'success': True,
                'is_favorite': notebook.is_favorite,
                'message': f'「{notebook.title}」を{status}しました'
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"お気に入り切り替えエラー: {e}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': 'お気に入りの切り替えに失敗しました'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': '無効なリクエストです'}, status=405)


@login_required
def toggle_bookmark_view(request, entry_pk):
    """エントリーのブックマーク切り替え"""
    if request.method == 'POST':
        try:
            entry = get_object_or_404(Entry, pk=entry_pk, notebook__user=request.user)
            entry.is_bookmarked = not entry.is_bookmarked
            entry.save(update_fields=['is_bookmarked'])
            
            status = 'ブックマークに追加' if entry.is_bookmarked else 'ブックマークから削除'
            return JsonResponse({
                'success': True,
                'is_bookmarked': entry.is_bookmarked,
                'message': f'「{entry.title}」を{status}しました'
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"ブックマーク切り替えエラー: {e}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'error': 'ブックマークの切り替えに失敗しました'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': '無効なリクエストです'}, status=405)


@login_required
def sub_notebook_create_ajax(request, notebook_pk):
    """サブノート作成Ajax"""
    if request.method == 'POST':
        try:
            notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
            data = json.loads(request.body)
            
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            
            if not title:
                return JsonResponse({
                    'success': False,
                    'error': 'サブノート名は必須です'
                }, status=400)
            
            # 重複チェック
            if SubNotebook.objects.filter(notebook=notebook, title=title).exists():
                return JsonResponse({
                    'success': False,
                    'error': '同名のサブノートが既に存在します'
                }, status=400)
            
            # サブノート作成
            sub_notebook = SubNotebook.objects.create(
                notebook=notebook,
                title=title,
                description=description,
                order=notebook.sub_notebooks.count()
            )
            
            return JsonResponse({
                'success': True,
                'sub_notebook': {
                    'id': str(sub_notebook.pk),
                    'title': sub_notebook.title,
                    'description': sub_notebook.description
                },
                'message': f'サブノート「{title}」を作成しました'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '無効なJSONデータです'
            }, status=400)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"サブノート作成エラー: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'サブノートの作成に失敗しました'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': '無効なリクエストです'}, status=405)


@login_required
def get_template_ajax(request, template_pk):
    """テンプレート情報をAjaxで取得"""
    try:
        template = get_object_or_404(NotebookTemplate, pk=template_pk, is_active=True)
        
        return JsonResponse({
            'success': True,
            'template': {
                'name': template.name,
                'description': template.description,
                'default_title': template.default_title,
                'default_strategy': template.default_strategy,
                'default_criteria': template.default_criteria,
                'suggested_sub_notebooks': template.suggested_sub_notebooks,
                'suggested_tags': template.suggested_tags
            }
        })
        
    except NotebookTemplate.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'テンプレートが見つかりません'
        }, status=404)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"テンプレート取得エラー: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'テンプレートの取得に失敗しました'
        }, status=500)


@login_required
def notebook_search_ajax(request):
    """ノートブック検索Ajax（リアルタイム検索用）"""
    query = request.GET.get('q', '').strip()
    filters = {
        'notebook_type': request.GET.get('notebook_type', ''),
        'status': request.GET.get('status', ''),
        'is_favorite': request.GET.get('is_favorite') == 'true'
    }
    
    try:
        # 基本クエリセット
        queryset = Notebook.objects.filter(user=request.user)
        
        # 検索クエリの適用
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(subtitle__icontains=query) |
                Q(description__icontains=query) |
                Q(investment_strategy__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        
        # フィルターの適用
        if filters['notebook_type']:
            queryset = queryset.filter(notebook_type=filters['notebook_type'])
        
        if filters['status']:
            queryset = queryset.filter(status=filters['status'])
            
        if filters['is_favorite']:
            queryset = queryset.filter(is_favorite=True)
        
        # 統計情報付きで取得
        queryset = queryset.annotate(
            recent_entries_count=Count(
                'entries',
                filter=Q(entries__created_at__gte=timezone.now() - timedelta(days=30))
            ),
            stock_count=Count('entries__stock_code', distinct=True)
        ).select_related().prefetch_related('tags')[:20]  # 最大20件
        
        # 結果をシリアライズ
        results = []
        for notebook in queryset:
            results.append({
                'id': str(notebook.pk),
                'title': notebook.title,
                'subtitle': notebook.subtitle,
                'notebook_type': notebook.get_notebook_type_display(),
                'status': notebook.get_status_display(),
                'status_code': notebook.status,
                'entry_count': notebook.entry_count,
                'recent_entries_count': notebook.recent_entries_count,
                'stock_count': notebook.stock_count,
                'is_favorite': notebook.is_favorite,
                'updated_at': notebook.updated_at.isoformat(),
                'tags': [{'id': tag.pk, 'name': tag.name} for tag in notebook.tags.all()],
                'url': reverse('notes:detail', kwargs={'pk': notebook.pk})
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results),
            'query': query
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"ノートブック検索エラー: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': '検索処理中にエラーが発生しました'
        }, status=500)


@login_required
def entry_search_ajax(request, notebook_pk):
    """エントリー検索Ajax（サブノート・フィルター用）"""
    notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
    
    # フィルターパラメータ
    filters = {
        'sub_notebook': request.GET.get('sub_notebook', ''),
        'entry_type': request.GET.get('entry_type', ''),
        'stock_code': request.GET.get('stock_code', ''),
        'is_important': request.GET.get('is_important') == 'true',
        'is_bookmarked': request.GET.get('is_bookmarked') == 'true',
        'query': request.GET.get('q', '').strip()
    }
    
    try:
        # 基本クエリセット
        queryset = notebook.entries.select_related('sub_notebook').prefetch_related('tags')
        
        # フィルターの適用
        if filters['sub_notebook']:
            queryset = queryset.filter(sub_notebook_id=filters['sub_notebook'])
        
        if filters['entry_type']:
            queryset = queryset.filter(entry_type=filters['entry_type'])
        
        if filters['stock_code']:
            queryset = queryset.filter(stock_code=filters['stock_code'])
        
        if filters['is_important']:
            queryset = queryset.filter(is_important=True)
        
        if filters['is_bookmarked']:
            queryset = queryset.filter(is_bookmarked=True)
        
        # テキスト検索
        if filters['query']:
            queryset = queryset.filter(
                Q(title__icontains=filters['query']) |
                Q(stock_code__icontains=filters['query']) |
                Q(company_name__icontains=filters['query'])
            )
        
        # ソート
        sort_order = request.GET.get('sort', 'newest')
        if sort_order == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort_order == 'important':
            queryset = queryset.order_by('-is_important', '-created_at')
        elif sort_order == 'stock':
            queryset = queryset.order_by('stock_code', '-created_at')
        else:  # newest
            queryset = queryset.order_by('-created_at')
        
        # ページネーション
        page_number = request.GET.get('page', 1)
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)
        
        # 結果をシリアライズ
        results = []
        for entry in page_obj:
            results.append({
                'id': str(entry.pk),
                'title': entry.title,
                'entry_type': entry.entry_type,
                'entry_type_display': entry.get_entry_type_display(),
                'stock_code': entry.stock_code,
                'company_name': entry.company_name,
                'stock_display': entry.get_stock_display(),
                'sub_notebook': {
                    'id': str(entry.sub_notebook.pk) if entry.sub_notebook else None,
                    'title': entry.sub_notebook.title if entry.sub_notebook else None
                },
                'is_important': entry.is_important,
                'is_bookmarked': entry.is_bookmarked,
                'created_at': entry.created_at.isoformat(),
                'tags': [{'id': tag.pk, 'name': tag.name} for tag in entry.tags.all()],
                'content_preview': generate_content_preview(entry)
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'pagination': {
                'page': page_obj.number,
                'num_pages': page_obj.paginator.num_pages,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'count': page_obj.paginator.count
            },
            'filters': filters
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"エントリー検索エラー: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': '検索処理中にエラーが発生しました'
        }, status=500)


def generate_content_preview(entry):
    """エントリーコンテンツのプレビューを生成"""
    content = entry.content
    entry_type = entry.entry_type
    
    if entry_type == 'ANALYSIS' and content.get('summary'):
        return content['summary'][:100] + '...' if len(content['summary']) > 100 else content['summary']
    elif entry_type == 'NEWS' and content.get('headline'):
        return content['headline']
    elif entry_type == 'CALCULATION' and content.get('current_price'):
        return f"現在株価: {content['current_price']}"
    elif entry_type == 'MEMO' and content.get('observation'):
        return content['observation'][:100] + '...' if len(content['observation']) > 100 else content['observation']
    elif entry_type == 'GOAL' and content.get('target_price'):
        return f"目標株価: {content['target_price']}"
    
    return "詳細はクリックして確認してください"