# ========================================
# apps/dashboard/admin.py
# ========================================

from django.contrib import admin
from apps.dashboard.models import DashboardStats, RecentActivity

@admin.register(DashboardStats)
class DashboardStatsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'active_notebooks', 'monthly_entries', 
        'total_entries', 'goal_achievement_rate', 'updated_at'
    ]
    list_filter = ['updated_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('ユーザー', {
            'fields': ('user',)
        }),
        ('統計情報', {
            'fields': (
                'active_notebooks', 'monthly_entries', 
                'total_entries', 'goal_achievement_rate'
            )
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(RecentActivity)
class RecentActivityAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'activity_type', 'title', 'created_at'
    ]
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__username', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('アクティビティ情報', {
            'fields': ('user', 'activity_type', 'title', 'description')
        }),
        ('関連データ', {
            'fields': ('related_object_id',)
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
