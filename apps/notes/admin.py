# ========================================
# apps/notes/admin.py
# ========================================

from django.contrib import admin
from django.utils.html import format_html
from apps.notes.models import Notebook, Entry

class EntryInline(admin.TabularInline):
    model = Entry
    extra = 0
    fields = ['entry_type', 'title', 'created_at']
    readonly_fields = ['created_at']
    can_delete = True

@admin.register(Notebook)
class NotebookAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 
        'status', 'entry_count', 'updated_at'
    ]
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['title']
    filter_horizontal = ['tags']
    
    inlines = [EntryInline]
    
    readonly_fields = ['id', 'entry_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('user', 'title', 'status')
        }),
        ('銘柄情報', {
            'fields': ('stock_code', 'company_name')
        }),
        ('投資目標', {
            'fields': ('target_price', 'sell_timing', 'investment_reason')
        }),
        ('詳細', {
            'fields': ('key_criteria', 'risk_factors', 'tags'),
            'classes': ('collapse',)
        }),
        ('メタデータ', {
            'fields': ('id', 'entry_count', 'is_public'),
            'classes': ('collapse',)
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """クエリセットを最適化"""
        return super().get_queryset(request).select_related('user').prefetch_related('tags')

@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'notebook_title', 'entry_type', 
        'created_at', 'tags_display'
    ]
    list_filter = ['entry_type', 'created_at']
    search_fields = ['title', 'notebook__title']
    filter_horizontal = ['tags']
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('notebook', 'entry_type', 'title')
        }),
        ('コンテンツ', {
            'fields': ('content', 'tags')
        }),
        ('メタデータ', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def notebook_title(self, obj):
        """関連ノートブックのタイトルを表示"""
        return obj.notebook.title
    notebook_title.short_description = 'ノートブック'
    
    def tags_display(self, obj):
        """タグを見やすく表示"""
        tags = obj.tags.all()[:3]  # 最初の3つのタグを表示
        if tags:
            tag_names = [tag.name for tag in tags]
            result = ', '.join(tag_names)
            if obj.tags.count() > 3:
                result += f' (+{obj.tags.count() - 3})'
            return result
        return '-'
    tags_display.short_description = 'タグ'