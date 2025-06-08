# ========================================
# apps/accounts/models.py
# ========================================

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from apps.common.models import BaseModel

class UserProfile(BaseModel):
    """ユーザープロフィール拡張"""
    
    INVESTMENT_EXPERIENCE_CHOICES = [
        ('BEGINNER', '初心者（1年未満）'),
        ('INTERMEDIATE', '中級者（1-5年）'),
        ('ADVANCED', '上級者（5年以上）'),
        ('EXPERT', 'エキスパート（10年以上）'),
    ]
    
    INVESTMENT_STYLE_CHOICES = [
        ('CONSERVATIVE', '保守的'),
        ('MODERATE', '中庸'),
        ('AGGRESSIVE', '積極的'),
        ('SPECULATIVE', '投機的'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='ユーザー'
    )
    display_name = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='表示名',
        help_text='空の場合はユーザー名が表示されます'
    )
    bio = models.TextField(
        max_length=500, 
        blank=True, 
        verbose_name='自己紹介',
        help_text='投資経験や関心分野など（最大500文字）'
    )
    investment_experience = models.CharField(
        max_length=20,
        choices=INVESTMENT_EXPERIENCE_CHOICES,
        default='BEGINNER',
        verbose_name='投資経験'
    )
    investment_style = models.CharField(
        max_length=20,
        choices=INVESTMENT_STYLE_CHOICES,
        default='MODERATE',
        verbose_name='投資スタイル'
    )
    
    # 設定項目
    email_notifications = models.BooleanField(
        default=True, 
        verbose_name='メール通知を受け取る'
    )
    public_profile = models.BooleanField(
        default=False, 
        verbose_name='プロフィールを公開する'
    )
    show_statistics = models.BooleanField(
        default=True, 
        verbose_name='統計情報を表示する'
    )
    
    # アクティビティ追跡
    last_login_ip = models.GenericIPAddressField(
        null=True, 
        blank=True, 
        verbose_name='最終ログインIP'
    )
    total_notebooks = models.PositiveIntegerField(
        default=0, 
        verbose_name='作成ノート数'
    )
    total_entries = models.PositiveIntegerField(
        default=0, 
        verbose_name='作成エントリー数'
    )
    
    class Meta:
        verbose_name = 'ユーザープロフィール'
        verbose_name_plural = 'ユーザープロフィール'
    
    def __str__(self):
        return f"{self.user.username}のプロフィール"
    
    def get_display_name(self):
        """表示名を取得（設定されていない場合はユーザー名）"""
        return self.display_name or self.user.username
    
    def update_statistics(self):
        """統計情報を更新"""
        from apps.notes.models import Notebook, Entry
        
        self.total_notebooks = Notebook.objects.filter(user=self.user).count()
        self.total_entries = Entry.objects.filter(notebook__user=self.user).count()
        self.save(update_fields=['total_notebooks', 'total_entries'])


class UserSettings(BaseModel):
    """ユーザー設定"""
    
    THEME_CHOICES = [
        ('DARK', 'ダークテーマ'),
        ('LIGHT', 'ライトテーマ'),
        ('AUTO', 'システム設定に従う'),
    ]
    
    LANGUAGE_CHOICES = [
        ('ja', '日本語'),
        ('en', 'English'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='ユーザー'
    )
    
    # 表示設定
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='DARK',
        verbose_name='テーマ'
    )
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='ja',
        verbose_name='言語'
    )
    items_per_page = models.PositiveIntegerField(
        default=12,
        verbose_name='1ページあたりの表示件数'
    )
    
    # ダッシュボード設定
    show_recent_activity = models.BooleanField(
        default=True, 
        verbose_name='最近のアクティビティを表示'
    )
    show_trending_tags = models.BooleanField(
        default=True, 
        verbose_name='トレンドタグを表示'
    )
    show_statistics = models.BooleanField(
        default=True, 
        verbose_name='統計情報を表示'
    )
    
    # 通知設定
    price_alert_enabled = models.BooleanField(
        default=True, 
        verbose_name='株価アラートを有効にする'
    )
    news_notification_enabled = models.BooleanField(
        default=True, 
        verbose_name='ニュース通知を有効にする'
    )
    
    class Meta:
        verbose_name = 'ユーザー設定'
        verbose_name_plural = 'ユーザー設定'
    
    def __str__(self):
        return f"{self.user.username}の設定"


class LoginHistory(BaseModel):
    """ログイン履歴"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='ユーザー'
    )
    ip_address = models.GenericIPAddressField(verbose_name='IPアドレス')
    user_agent = models.TextField(verbose_name='ユーザーエージェント')
    success = models.BooleanField(default=True, verbose_name='成功')
    
    class Meta:
        verbose_name = 'ログイン履歴'
        verbose_name_plural = 'ログイン履歴'
        ordering = ['-created_at']
    
    def __str__(self):
        status = '成功' if self.success else '失敗'
        return f"{self.user.username} - {status} ({self.created_at})"