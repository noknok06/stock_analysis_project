from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count
from apps.notes.models import Notebook, SubNotebook, Entry, EntryRelation

class SubNotebookInline(admin.TabularInline):
    """サブノートのインライン表示"""
    model = SubNotebook
    extra = 0
    fields = ['title', 'description', 'order_index', 'entry_count']
    readonly_fields = ['entry_count']
    ordering = ['order_index']

class EntryInline(admin.TabularInline):
    """エントリーのインライン表示（最新5件のみ）"""
    model = Entry
    extra = 0
    fields = ['title', 'entry_type', 'stock_code', 'is_bookmarked', 'importance', 'created_at']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        """最新5件のみ表示"""
        return super().get_queryset(request)[:5]

@admin.register(Notebook)
class NotebookAdmin(admin.ModelAdmin):
    """ノートブック管理画面"""
    
    list_display = [
        'title', 'user', 'notebook_type', 'status', 
        'entry_count_display', 'stock_count_display', 
        'last_entry_date', 'created_at'
    ]
    list_filter = [
        'notebook_type', 'status', 'created_at', 'updated_at',
        'is_public'
    ]
    search_fields = [
        'title', 'subtitle', 'description', 'user__username',
        'user__email'
    ]
    filter_horizontal = ['tags']
    
    inlines = [SubNotebookInline, EntryInline]
    
    readonly_fields = [
        'id', 'entry_count', 'stock_count', 'last_entry_date',
        'created_at', 'updated_at', 'stock_list_display'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('user', 'title', 'subtitle', 'description')
        }),
        ('分類・設定', {
            'fields': ('notebook_type', 'status', 'is_public')
        }),
        ('目標・テーマ', {
            'fields': ('objectives', 'key_themes', 'notes'),
            'classes': ('collapse',)
        }),
        ('統計情報', {
            'fields': (
                'entry_count', 'stock_count', 'last_entry_date',
                'stock_list_display'
            ),
            'classes': ('collapse',)
        }),
        ('タグ', {
            'fields': ('tags',)
        }),
        ('メタデータ', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # カスタム表示メソッド
    def entry_count_display(self, obj):
        """エントリー数の表示"""
        count = obj.entry_count
        if count > 0:
            url = reverse('admin:notes_entry_changelist') + f'?notebook__id__exact={obj.pk}'
            return format_html(
                '<a href="{}">{} 件</a>',
                url, count
            )
        return '0 件'
    entry_count_display.short_description = 'エントリー数'
    
    def stock_count_display(self, obj):
        """銘柄数の表示"""
        return f'{obj.stock_count} 銘柄'
    stock_count_display.short_description = '銘柄数'
    
    def stock_list_display(self, obj):
        """対象銘柄一覧の表示"""
        stock_list = obj.get_stock_list()
        if stock_list:
            stocks = []
            for stock in stock_list[:10]:  # 最大10件まで表示
                if stock['company_name']:
                    stocks.append(f"{stock['stock_code']} {stock['company_name']}")
                else:
                    stocks.append(stock['stock_code'])
            
            result = ', '.join(stocks)
            if len(stock_list) > 10:
                result += f' ...他{len(stock_list) - 10}件'
            return result
        return '銘柄なし'
    stock_list_display.short_description = '対象銘柄'
    
    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related('user').prefetch_related('tags')

@admin.register(SubNotebook)
class SubNotebookAdmin(admin.ModelAdmin):
    """サブノート管理画面"""
    
    list_display = [
        'title', 'notebook_link', 'order_index', 
        'entry_count', 'created_at'
    ]
    list_filter = ['created_at', 'notebook__notebook_type']
    search_fields = ['title', 'description', 'notebook__title']
    list_editable = ['order_index']
    
    readonly_fields = ['entry_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('notebook', 'title', 'description', 'order_index')
        }),
        ('統計', {
            'fields': ('entry_count',)
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def notebook_link(self, obj):
        """親ノートブックへのリンク"""
        url = reverse('admin:notes_notebook_change', args=[obj.notebook.pk])
        return format_html('<a href="{}">{}</a>', url, obj.notebook.title)
    notebook_link.short_description = 'ノートブック'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('notebook')

@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    """エントリー管理画面"""
    
    list_display = [
        'title', 'notebook_link', 'entry_type', 
        'stock_info_display', 'importance_stars',
        'bookmark_status', 'created_at'
    ]
    list_filter = [
        'entry_type', 'is_bookmarked', 'importance',
        'created_at', 'notebook__notebook_type',
        'stock_code'
    ]
    search_fields = [
        'title', 'summary', 'stock_code', 'company_name',
        'notebook__title'
    ]
    filter_horizontal = ['tags']
    list_editable = ['importance', 'is_bookmarked']
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'content_preview'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('notebook', 'sub_notebook', 'title', 'entry_type')
        }),
        ('銘柄情報', {
            'fields': (
                'stock_code', 'company_name', 'market',
                'current_price', 'target_price', 'rating'
            )
        }),
        ('イベント情報', {
            'fields': ('event_date', 'event_type'),
            'classes': ('collapse',)
        }),
        ('コンテンツ', {
            'fields': ('summary', 'content', 'content_preview')
        }),
        ('メタ情報', {
            'fields': ('importance', 'is_bookmarked', 'tags')
        }),
        ('タイムスタンプ', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # カスタム表示メソッド
    def notebook_link(self, obj):
        """ノートブックへのリンク"""
        url = reverse('admin:notes_notebook_change', args=[obj.notebook.pk])
        return format_html('<a href="{}">{}</a>', url, obj.notebook.title)
    notebook_link.short_description = 'ノートブック'
    
    def stock_info_display(self, obj):
        """銘柄情報の表示"""
        if obj.stock_code:
            parts = [obj.stock_code]
            if obj.company_name:
                parts.append(obj.company_name)
            if obj.current_price:
                parts.append(f'¥{obj.current_price}')
            return ' '.join(parts)
        return '-'
    stock_info_display.short_description = '銘柄情報'
    
    def importance_stars(self, obj):
        """重要度の星表示"""
        stars = '★' * obj.importance + '☆' * (5 - obj.importance)
        return stars
    importance_stars.short_description = '重要度'
    
    def bookmark_status(self, obj):
        """ブックマーク状態の表示"""
        if obj.is_bookmarked:
            return format_html('<span style="color: gold;">📌</span>')
        return '-'
    bookmark_status.short_description = 'ブックマーク'
    
    def content_preview(self, obj):
        """コンテンツプレビュー"""
        if obj.summary:
            preview = obj.summary[:200]
            if len(obj.summary) > 200:
                preview += '...'
            return format_html('<div style="max-width: 500px;">{}</div>', preview)
        return 'サマリーなし'
    content_preview.short_description = 'コンテンツプレビュー'
    
    def get_queryset(self, request):
        """クエリセットの最適化"""
        return super().get_queryset(request).select_related(
            'notebook', 'sub_notebook'
        ).prefetch_related('tags')

@admin.register(EntryRelation)
class EntryRelationAdmin(admin.ModelAdmin):
    """エントリー関連管理画面"""
    
    list_display = [
        'from_entry_link', 'relation_type', 'to_entry_link', 'created_at'
    ]
    list_filter = ['relation_type', 'created_at']
    search_fields = [
        'from_entry__title', 'to_entry__title', 'notes'
    ]
    
    fieldsets = (
        ('関連情報', {
            'fields': ('from_entry', 'to_entry', 'relation_type')
        }),
        ('詳細', {
            'fields': ('notes',)
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def from_entry_link(self, obj):
        """関連元エントリーへのリンク"""
        url = reverse('admin:notes_entry_change', args=[obj.from_entry.pk])
        return format_html('<a href="{}">{}</a>', url, obj.from_entry.title)
    from_entry_link.short_description = '関連元'
    
    def to_entry_link(self, obj):
        """関連先エントリーへのリンク"""
        url = reverse('admin:notes_entry_change', args=[obj.to_entry.pk])
        return format_html('<a href="{}">{}</a>', url, obj.to_entry.title)
    to_entry_link.short_description = '関連先'
    
    # ========================================
# カスタム管理アクション
# ========================================

@admin.action(description='選択されたノートブックをアーカイブ')
def archive_notebooks(modeladmin, request, queryset):
    """ノートブックの一括アーカイブ"""
    updated = queryset.update(status='ARCHIVED')
    modeladmin.message_user(
        request,
        f'{updated} 件のノートブックをアーカイブしました。'
    )

@admin.action(description='選択されたエントリーをブックマーク')
def bookmark_entries(modeladmin, request, queryset):
    """エントリーの一括ブックマーク"""
    updated = queryset.update(is_bookmarked=True)
    modeladmin.message_user(
        request,
        f'{updated} 件のエントリーをブックマークしました。'
    )

@admin.action(description='選択されたエントリーの重要度を最高に設定')
def set_high_importance(modeladmin, request, queryset):
    """エントリーの重要度を最高に設定"""
    updated = queryset.update(importance=5)
    modeladmin.message_user(
        request,
        f'{updated} 件のエントリーの重要度を最高に設定しました。'
    )

# アクションを管理クラスに追加
NotebookAdmin.actions = [archive_notebooks]
EntryAdmin.actions = [bookmark_entries, set_high_importance]

# ========================================
# 管理画面の設定カスタマイズ
# ========================================

# 管理画面のタイトル・ヘッダーカスタマイズ
admin.site.site_header = '株式分析記録アプリ 管理画面'
admin.site.site_title = '株式分析記録アプリ'
admin.site.index_title = 'ダッシュボード'