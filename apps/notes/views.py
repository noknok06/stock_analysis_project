# ========================================
# apps/notes/views.py
# ========================================

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from apps.notes.models import Notebook, Entry
from apps.notes.forms import NotebookForm, EntryForm, SearchForm
from apps.common.mixins import UserOwnerMixin, SearchMixin
from apps.notes.services import NotebookService
from apps.common.utils import ContentHelper, TagHelper


class NotebookListView(UserOwnerMixin, SearchMixin, ListView):
    """ノート一覧ビュー"""
    model = Notebook
    template_name = 'notes/index.html'
    context_object_name = 'notebooks'
    paginate_by = 12
    search_fields = ['title', 'subtitle', 'company_name', 'investment_reason']
    
    def get_queryset(self):
        """検索とフィルタリングを適用したクエリセット"""
        queryset = super().get_queryset()
        queryset = self.apply_search(queryset)
        
        # ステータスフィルター
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # タグフィルター
        tag_ids = self.request.GET.getlist('tags')
        if tag_ids:
            queryset = queryset.filter(tags__in=tag_ids).distinct()
        
        return queryset.select_related().prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        """コンテキストデータを追加"""
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        context['search_query'] = self.get_search_query()
        return context


class NotebookDetailView(UserOwnerMixin, DetailView):
    """ノート詳細ビュー"""
    model = Notebook
    template_name = 'notes/detail.html'
    context_object_name = 'notebook'
    
    def get_context_data(self, **kwargs):
        """エントリー一覧をページネーション付きで追加"""
        context = super().get_context_data(**kwargs)
        
        # エントリー一覧をページネーションで取得
        entries_list = self.object.entries.order_by('-created_at')
        paginator = Paginator(entries_list, 5)  # 1ページ5エントリー
        
        page_number = self.request.GET.get('page')
        entries = paginator.get_page(page_number)
        
        context['entries'] = entries
        context['is_paginated'] = entries.has_other_pages()
        context['page_obj'] = entries
        return context


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
    """ノート編集ビュー"""
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
    """エントリー作成ビュー"""
    notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
    
    if request.method == 'POST':
        try:
            # フォームデータを処理
            entry_type = request.POST.get('entry_type')
            title = request.POST.get('title')
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
            
            # エントリーを作成
            entry = Entry.objects.create(
                notebook=notebook,
                entry_type=entry_type,
                title=title,
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
            'created_at': entry.created_at.strftime('%Y/%m/%d %H:%M'),
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
def entry_update_view(request, entry_pk):
    """エントリー更新ビュー"""
    entry = get_object_or_404(Entry, pk=entry_pk, notebook__user=request.user)
    
    if request.method == 'POST':
        try:
            # 更新処理
            entry.title = request.POST.get('title', entry.title)
            content_json = request.POST.get('content', '{}')
            
            try:
                content_data = json.loads(content_json)
                entry.content = ContentHelper.format_json_content(content_data, entry.entry_type)
                entry.save()
                
                messages.success(request, f'エントリー「{entry.title}」を更新しました。')
                
            except json.JSONDecodeError:
                messages.error(request, '無効なデータ形式です。')
                
        except Exception as e:
            messages.error(request, f'エントリーの更新に失敗しました: {str(e)}')
    
    return redirect('notes:detail', pk=entry.notebook.pk)


@login_required
def entry_delete_view(request, entry_pk):
    """エントリー削除ビュー"""
    entry = get_object_or_404(Entry, pk=entry_pk, notebook__user=request.user)
    notebook_pk = entry.notebook.pk
    
    if request.method == 'POST':
        try:
            entry_title = entry.title
            entry.delete()
            
            # ノートブックのエントリー数を更新
            entry.notebook.entry_count = entry.notebook.entries.count()
            entry.notebook.save(update_fields=['entry_count'])
            
            messages.success(request, f'エントリー「{entry_title}」を削除しました。')
            
        except Exception as e:
            messages.error(request, f'エントリーの削除に失敗しました: {str(e)}')
    
    return redirect('notes:detail', pk=notebook_pk)


# ========================================
# ヘルパー関数
# ========================================

def render_entry_content_html(entry):
    """エントリータイプに応じたHTMLコンテンツを生成"""
    content = entry.content
    entry_type = entry.entry_type
    
    if entry_type == 'ANALYSIS':
        return render_analysis_content(content)
    elif entry_type == 'NEWS':
        return render_news_content(content)
    elif entry_type == 'CALCULATION':
        return render_calculation_content(content)
    elif entry_type == 'MEMO':
        return render_memo_content(content)
    elif entry_type == 'GOAL':
        return render_goal_content(content)
    else:
        return f'<p class="text-gray-300">コンテンツが見つかりません。</p>'


def render_analysis_content(content):
    """決算分析コンテンツのHTML生成"""
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
    """ニュースコンテンツのHTML生成"""
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
    """計算結果コンテンツのHTML生成"""
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
    """メモコンテンツのHTML生成"""
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
    """投資目標コンテンツのHTML生成"""
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