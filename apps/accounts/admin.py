# ========================================
# apps/accounts/admin.py
# ========================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from apps.accounts.models import UserProfile, UserSettings, LoginHistory

# ユーザー管理のカスタマイズ
class UserProfileInline(admin.StackedInline):
    """ユーザープロフィールのインライン表示"""
    model = UserProfile
    can_delete = False
    verbose_name = 'プロフィール'
    verbose_name_plural = 'プロフィール'
    
    fieldsets = (
        ('基本情報', {
            'fields': ('display_name', 'bio', 'investment_experience', 'investment_style')
        }),
        ('設定', {
            'fields': ('email_notifications', 'public_profile', 'show_statistics'),
            'classes': ('collapse',)
        }),
        ('統計', {
            'fields': ('total_notebooks', 'total_entries', 'last_login_ip'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('total_notebooks', 'total_entries', 'last_login_ip')


class UserSettingsInline(admin.StackedInline):
    """ユーザー設定のインライン表示"""
    model = UserSettings
    can_delete = False
    verbose_name = '表示設定'
    verbose_name_plural = '表示設定'
    
    fieldsets = (
        ('表示設定', {
            'fields': ('theme', 'language', 'items_per_page')
        }),
        ('ダッシュボード', {
            'fields': ('show_recent_activity', 'show_trending_tags', 'show_statistics'),
            'classes': ('collapse',)
        }),
        ('通知設定', {
            'fields': ('price_alert_enabled', 'news_notification_enabled'),
            'classes': ('collapse',)
        }),
    )


class CustomUserAdmin(BaseUserAdmin):
    """カスタムユーザー管理"""
    inlines = (UserProfileInline, UserSettingsInline)
    
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'is_active', 'is_staff', 'get_investment_experience',
        'get_total_notebooks', 'date_joined'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'date_joined',
        'userprofile__investment_experience', 'userprofile__investment_style'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    def get_investment_experience(self, obj):
        """投資経験を表示"""
        try:
            return obj.userprofile.get_investment_experience_display()
        except UserProfile.DoesNotExist:
            return '-'
    get_investment_experience.short_description = '投資経験'
    
    def get_total_notebooks(self, obj):
        """ノート数を表示"""
        try:
            return obj.userprofile.total_notebooks
        except UserProfile.DoesNotExist:
            return 0
    get_total_notebooks.short_description = 'ノート数'


# 既存のUserAdminを置き換え
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """ユーザープロフィール管理"""
    list_display = [
        'user', 'display_name', 'investment_experience', 
        'investment_style', 'total_notebooks', 'total_entries',
        'public_profile', 'updated_at'
    ]
    list_filter = [
        'investment_experience', 'investment_style', 
        'public_profile', 'email_notifications', 'created_at'
    ]
    search_fields = ['user__username', 'user__email', 'display_name', 'bio']
    readonly_fields = ['created_at', 'updated_at', 'total_notebooks', 'total_entries']
    
    fieldsets = (
        ('ユーザー', {
            'fields': ('user',)
        }),
        ('基本情報', {
            'fields': ('display_name', 'bio')
        }),
        ('投資プロフィール', {
            'fields': ('investment_experience', 'investment_style')
        }),
        ('設定', {
            'fields': ('email_notifications', 'public_profile', 'show_statistics')
        }),
        ('アクティビティ', {
            'fields': ('last_login_ip', 'total_notebooks', 'total_entries'),
            'classes': ('collapse',)
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """クエリセットを最適化"""
        return super().get_queryset(request).select_related('user')


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    """ユーザー設定管理"""
    list_display = [
        'user', 'theme', 'language', 'items_per_page',
        'show_recent_activity', 'price_alert_enabled', 'updated_at'
    ]
    list_filter = [
        'theme', 'language', 'show_recent_activity', 
        'show_trending_tags', 'price_alert_enabled'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('ユーザー', {
            'fields': ('user',)
        }),
        ('表示設定', {
            'fields': ('theme', 'language', 'items_per_page')
        }),
        ('ダッシュボード設定', {
            'fields': ('show_recent_activity', 'show_trending_tags', 'show_statistics')
        }),
        ('通知設定', {
            'fields': ('price_alert_enabled', 'news_notification_enabled')
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """ログイン履歴管理"""
    list_display = [
        'user', 'ip_address', 'success', 'created_at', 'user_agent_short'
    ]
    list_filter = ['success', 'created_at']
    search_fields = ['user__username', 'user__email', 'ip_address']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('ログイン情報', {
            'fields': ('user', 'success', 'ip_address')
        }),
        ('詳細', {
            'fields': ('user_agent',),
            'classes': ('collapse',)
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_agent_short(self, obj):
        """短縮されたユーザーエージェント"""
        if len(obj.user_agent) > 50:
            return obj.user_agent[:50] + '...'
        return obj.user_agent
    user_agent_short.short_description = 'ユーザーエージェント'
    
    def has_add_permission(self, request):
        """追加権限を無効化"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """変更権限を無効化"""
        return False


# 管理画面のカスタマイズ
admin.site.site_header = '株式分析記録アプリ 管理画面'
admin.site.site_title = '管理画面'
admin.site.index_title = 'アプリケーション管理'