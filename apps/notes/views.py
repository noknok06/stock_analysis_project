# ========================================
# apps/notes/views.py
# ========================================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from apps.notes.models import Notebook, Entry
from apps.notes.forms import NotebookForm, EntryForm, SearchForm
from apps.common.mixins import UserOwnerMixin, SearchMixin
from apps.notes.services import NotebookService

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
        """エントリー一覧を追加"""
        context = super().get_context_data(**kwargs)
        entries = self.object.entries.order_by('-created_at')
        context['entries'] = entries
        context['entry_count'] = entries.count()
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
            return response
        except Exception as e:
            messages.error(self.request, 'ノートの作成に失敗しました。')
            return self.form_invalid(form)


class NotebookUpdateView(UserOwnerMixin, UpdateView):
    """ノート編集ビュー"""
    model = Notebook
    form_class = NotebookForm
    template_name = 'notes/edit.html'
    
    def get_success_url(self):
        return reverse_lazy('notes:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """フォーム有効時の処理"""
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'ノート「{self.object.title}」を更新しました。')
            return response
        except Exception as e:
            messages.error(self.request, 'ノートの更新に失敗しました。')
            return self.form_invalid(form)
