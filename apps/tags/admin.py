# ========================================
# apps/tags/admin.py
# ========================================

from django.contrib import admin
from apps.tags.models import Tag

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'usage_count', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['-usage_count', 'name']
    
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'category', 'description')
        }),
        ('統計', {
            'fields': ('usage_count', 'is_active')
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )