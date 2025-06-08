# ========================================
# apps/notes/views.py - 新しいノート構成対応ビュー
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
from django.utils import timezone

from apps.notes.models import Notebook, SubNotebook, Entry, EntryRelation
from apps.notes.forms import (
    NotebookTemplateChoiceForm, NotebookForm, SubNotebookForm, 
    EntryForm, QuickEntryForm, SearchForm
)
from apps.common.mixins import UserOwnerMixin, SearchMixin
from apps.common.utils import ContentHelper, TagHelper


# ========================================
# ノートブック関連ビュー
# ========================================

class NotebookListView(UserOwnerMixin, SearchMixin, ListView):
    """ノートブック一覧ビュー（新構造）"""
    model = Notebook
    template_name = 'notes/notebook_list.html'
    context_object_name = 'notebooks'
    paginate_by = 12
    search_fields = ['title', 'subtitle', 'description']
    
    def get_queryset(self):
        """検索とフィルタリングを適用"""
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
        
        # タグフィルター
        tag_ids = self.request.GET.getlist('tags')
        if tag_ids:
            queryset = queryset.filter(tags__in=tag_ids).distinct()
        
        return queryset.prefetch_related('tags', 'sub_notebooks').annotate(
            recent_entries_count=Count('entries', filter=Q(entries__created_at__gte=timezone.now().date()))
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        context['search_query'] = self.get_search_query()
        
        # 統計情報
        context['stats'] = {
            'total_notebooks': self.get_queryset().count(),
            'active_notebooks': self.get_queryset().filter(status='ACTIVE').count(),
            'total_entries': Entry.objects.filter(notebook__user=self.request.user).count(),
        }
        
        return context


class NotebookDetailView(UserOwnerMixin, DetailView):
    """ノートブック詳細ビュー（新構造）"""
    model = Notebook
    template_name = 'notes/notebook_detail.html'
    context_object_name = 'notebook'
    
    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'tags',
            Prefetch('sub_notebooks', queryset=SubNotebook.objects.order_by('order_index')),
            Prefetch('entries', queryset=Entry.objects.order_by('-created_at'))
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # エントリー一覧（ページネーション）
        entries_list = self.object.entries.order_by('-created_at')
        
        # エントリータイプフィルター
        entry_type = self.request.GET.get('entry_type')
        if entry_type:
            entries_list = entries_list.filter(entry_type=entry_type)
        
        # サブノートフィルター
        sub_notebook_id = self.request.GET.get('sub_notebook')
        if sub_notebook_id:
            entries_list = entries_list.filter(sub_notebook_id=sub_notebook_id)
        
        # ブックマークフィルター
        if self.request.GET.get('bookmarked'):
            entries_list = entries_list.filter(is_bookmarked=True)
        
        paginator = Paginator(entries_list, 10)
        page_number = self.request.GET.get('page')
        entries = paginator.get_page(page_number)
        
        context['entries'] = entries
        context['is_paginated'] = entries.has_other_pages()
        context['page_obj'] = entries
        
        # 銘柄一覧
        context['stock_list'] = self.object.get_stock_list()
        
        # サブノート一覧
        context['sub_notebooks'] = self.object.sub_notebooks.all()
        
        # フィルター情報
        context['current_filters'] = {
            'entry_type': entry_type,
            'sub_notebook': sub_notebook_id,
            'bookmarked': self.request.GET.get('bookmarked')
        }
        
        return context


@login_required
def notebook_template_selection_view(request):
    """ノート作成テンプレート選択ビュー"""
    if request.method == 'POST':
        form = NotebookTemplateChoiceForm(request.POST)
        if form.is_valid():
            template_type = form.cleaned_data['template_type']
            quick_title = form.cleaned_data.get('quick_title', '')
            
            # テンプレートに応じた初期データを準備
            initial_data = get_template_initial_data(template_type, quick_title)
            
            # ノート作成ページにリダイレクト
            return redirect('notes:create_with_template', template_type=template_type)
    else:
        form = NotebookTemplateChoiceForm()
    
    return render(request, 'notes/template_selection.html', {'form': form})


class NotebookCreateView(LoginRequiredMixin, CreateView):
    """ノートブック作成ビュー（新構造）"""
    model = Notebook
    form_class = NotebookForm
    template_name = 'notes/notebook_create.html'
    
    def get_initial(self):
        initial = super().get_initial()
        template_type = self.kwargs.get('template_type')
        
        if template_type:
            initial.update(get_template_initial_data(template_type))
        
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template_type'] = self.kwargs.get('template_type')
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # テンプレートに応じた初期サブノートを作成
        template_type = self.kwargs.get('template_type')
        if template_type:
            create_initial_sub_notebooks(self.object, template_type)
        
        messages.success(self.request, f'ノート「{self.object.title}」を作成しました。')
        return redirect('notes:detail', pk=self.object.pk)


class NotebookUpdateView(UserOwnerMixin, UpdateView):
    """ノートブック編集ビュー"""
    model = Notebook
    form_class = NotebookForm
    template_name = 'notes/notebook_edit.html'
    
    def get_success_url(self):
        return reverse_lazy('notes:detail', kwargs={'pk': self.object.pk})


# ========================================
# エントリー関連ビュー
# ========================================

class EntryListView(LoginRequiredMixin, ListView):
    """全エントリー一覧ビュー（横断検索）"""
    model = Entry
    template_name = 'notes/entry_list.html'
    context_object_name = 'entries'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Entry.objects.filter(notebook__user=self.request.user)
        
        # 検索
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(summary__icontains=q) |
                Q(stock_code__icontains=q) |
                Q(company_name__icontains=q) |
                Q(tags__name__icontains=q)
            ).distinct()
        
        # フィルター
        search_form = SearchForm(self.request.GET)
        if search_form.is_valid():
            if search_form.cleaned_data.get('entry_type'):
                queryset = queryset.filter(entry_type=search_form.cleaned_data['entry_type'])
            
            if search_form.cleaned_data.get('stock_code'):
                queryset = queryset.filter(stock_code=search_form.cleaned_data['stock_code'])
            
            if search_form.cleaned_data.get('date_from'):
                queryset = queryset.filter(created_at__gte=search_form.cleaned_data['date_from'])
            
            if search_form.cleaned_data.get('date_to'):
                queryset = queryset.filter(created_at__lte=search_form.cleaned_data['date_to'])
            
            if search_form.cleaned_data.get('bookmarked_only'):
                queryset = queryset.filter(is_bookmarked=True)
        
        return queryset.select_related('notebook', 'sub_notebook').prefetch_related('tags').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class EntryDetailView(LoginRequiredMixin, DetailView):
    """エントリー詳細ビュー"""
    model = Entry
    template_name = 'notes/entry_detail.html'
    context_object_name = 'entry'
    
    def get_queryset(self):
        return Entry.objects.filter(notebook__user=self.request.user).select_related(
            'notebook', 'sub_notebook'
        ).prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 関連エントリー
        context['related_entries'] = Entry.objects.filter(
            Q(stock_code=self.object.stock_code, stock_code__isnull=False) |
            Q(tags__in=self.object.tags.all())
        ).exclude(pk=self.object.pk).distinct()[:5]
        
        # 同じノート内の他エントリー
        context['notebook_entries'] = self.object.notebook.entries.exclude(
            pk=self.object.pk
        ).order_by('-created_at')[:5]
        
        return context


@login_required
def entry_create_view(request, notebook_pk):
    """エントリー作成ビュー（新構造）"""
    notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
    
    if request.method == 'POST':
        form = EntryForm(request.POST, notebook=notebook)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.notebook = notebook
            entry.save()
            form.save_m2m()
            
            messages.success(request, f'エントリー「{entry.title}」を作成しました。')
            return redirect('notes:detail', pk=notebook.pk)
    else:
        form = EntryForm(notebook=notebook)
    
    return render(request, 'notes/entry_create.html', {
        'form': form,
        'notebook': notebook
    })


@login_required
def entry_quick_create_view(request, notebook_pk):
    """クイックエントリー作成（Ajax対応）"""
    notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
    
    if request.method == 'POST':
        try:
            # フォームデータを処理
            title = request.POST.get('title')
            entry_type = request.POST.get('entry_type', 'MEMO')
            content_json = request.POST.get('content', '{}')
            stock_code = request.POST.get('stock_code', '')
            
            # エントリーを作成
            entry = Entry.objects.create(
                notebook=notebook,
                title=title,
                entry_type=entry_type,
                stock_code=stock_code,
                content=json.loads(content_json) if content_json else {},
                summary=request.POST.get('summary', '')
            )
            
            return JsonResponse({
                'success': True,
                'entry_id': str(entry.id),
                'message': 'エントリーを作成しました'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'error': '無効なリクエスト'}, status=400)


# ========================================
# サブノート関連ビュー
# ========================================

@login_required
def sub_notebook_create_view(request, notebook_pk):
    """サブノート作成ビュー"""
    notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
    
    if request.method == 'POST':
        form = SubNotebookForm(request.POST)
        if form.is_valid():
            sub_notebook = form.save(commit=False)
            sub_notebook.notebook = notebook
            sub_notebook.save()
            
            messages.success(request, f'サブノート「{sub_notebook.title}」を作成しました。')
            return redirect('notes:detail', pk=notebook.pk)
    else:
        form = SubNotebookForm()
    
    return render(request, 'notes/sub_notebook_create.html', {
        'form': form,
        'notebook': notebook
    })


@login_required
def sub_notebook_entries_view(request, notebook_pk, sub_notebook_pk):
    """サブノート内エントリー一覧ビュー"""
    notebook = get_object_or_404(Notebook, pk=notebook_pk, user=request.user)
    sub_notebook = get_object_or_404(SubNotebook, pk=sub_notebook_pk, notebook=notebook)
    
    entries = sub_notebook.entries.order_by('-created_at')
    
    paginator = Paginator(entries, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'notes/sub_notebook_entries.html', {
        'notebook': notebook,
        'sub_notebook': sub_notebook,
        'entries': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj
    })


# ========================================
# ヘルパー関数
# ========================================

def get_template_initial_data(template_type, quick_title=''):
    """テンプレートタイプに応じた初期データを取得"""
    template_data = {
        'theme_multi': {
            'notebook_type': 'THEME',
            'title': quick_title or '投資テーマ分析',
            'subtitle': '複数銘柄のテーマ別分析',
            'objectives': ['テーマ投資', '分散投資'],
            'key_themes': ['成長性', '持続可能性']
        },
        'watchlist': {
            'notebook_type': 'WATCHLIST',
            'title': quick_title or 'ウォッチリスト',
            'subtitle': '注目銘柄の監視',
            'objectives': ['市場監視', '投資機会発見'],
        },
        'portfolio': {
            'notebook_type': 'PORTFOLIO',
            'title': quick_title or 'ポートフォリオ管理',
            'subtitle': '保有銘柄の管理・分析',
            'objectives': ['資産管理', 'リスク分析'],
        },
        'sector_analysis': {
            'notebook_type': 'SECTOR',
            'title': quick_title or 'セクター分析',
            'subtitle': '業界・セクター別分析',
            'objectives': ['業界研究', '競合比較'],
        },
        'event_tracking': {
            'notebook_type': 'EVENT',
            'title': quick_title or 'イベント追跡',
            'subtitle': '決算・IR等イベント追跡',
            'objectives': ['イベント分析', 'タイミング投資'],
        },
        'research_project': {
            'notebook_type': 'RESEARCH',
            'title': quick_title or 'リサーチプロジェクト',
            'subtitle': '詳細調査・研究',
            'objectives': ['深堀り分析', '投資判断'],
        }
    }
    
    return template_data.get(template_type, {})


def create_initial_sub_notebooks(notebook, template_type):
    """テンプレートに応じた初期サブノートを作成"""
    sub_notebook_templates = {
        'theme_multi': [
            {'title': '日本株', 'description': '国内銘柄の分析', 'order_index': 1},
            {'title': '米国株', 'description': '米国銘柄の分析', 'order_index': 2},
            {'title': '新興国株', 'description': '新興国銘柄の分析', 'order_index': 3},
        ],
        'watchlist': [
            {'title': '高優先', 'description': '最優先監視銘柄', 'order_index': 1},
            {'title': '中優先', 'description': '中程度監視銘柄', 'order_index': 2},
            {'title': '低優先', 'description': '参考程度', 'order_index': 3},
        ],
        'sector_analysis': [
            {'title': '業界概要', 'description': '業界全体の分析', 'order_index': 1},
            {'title': '主要企業', 'description': 'リーディング企業', 'order_index': 2},
            {'title': '新興企業', 'description': '成長企業・スタートアップ', 'order_index': 3},
        ],
    }
    
    templates = sub_notebook_templates.get(template_type, [])
    for template in templates:
        SubNotebook.objects.create(
            notebook=notebook,
            **template
        )