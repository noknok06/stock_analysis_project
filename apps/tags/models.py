from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from apps.common.models import BaseModel

class TagManager(models.Manager):
    """タグマネージャー（ユーザー固有クエリセット）"""
    
    def get_for_user(self, user):
        """指定ユーザーのタグのみを取得"""
        return self.filter(user=user)
    
    def get_trending_tags(self, user, limit=10):
        """ユーザーのトレンドタグを取得（使用頻度とアクティビティベース）"""
        # 過去30日間でアクティブなタグを優先
        recent_threshold = timezone.now() - timedelta(days=30)
        
        return self.filter(
            user=user,
            is_active=True,
            usage_count__gt=0
        ).annotate(
            recent_usage=models.Count(
                'notebook',
                filter=models.Q(notebook__updated_at__gte=recent_threshold)
            ) + models.Count(
                'entry',
                filter=models.Q(entry__updated_at__gte=recent_threshold)
            )
        ).order_by(
            '-recent_usage',  # 最近の使用頻度順
            '-usage_count',   # 総使用回数順
            '-updated_at'     # 更新日時順
        )[:limit]
    
    def get_popular_tags(self, user, limit=20):
        """ユーザーの人気タグを取得（総使用回数ベース）"""
        return self.filter(
            user=user,
            is_active=True,
            usage_count__gt=0
        ).order_by('-usage_count', '-updated_at')[:limit]
    
    def search_tags(self, user, query):
        """ユーザーのタグを検索"""
        if not query:
            return self.none()
        
        return self.filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query),
            user=user,
            is_active=True
        ).order_by('-usage_count', 'name')


class Tag(BaseModel):
    """タグモデル（ユーザー固有版・カテゴリなし）"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='ユーザー',
        help_text='このタグの所有者'
    )
    name = models.CharField(max_length=50, verbose_name='タグ名')
    description = models.TextField(blank=True, verbose_name='説明')
    usage_count = models.PositiveIntegerField(default=0, verbose_name='使用回数')
    is_active = models.BooleanField(default=True, verbose_name='有効フラグ')
    color = models.CharField(max_length=7, blank=True, verbose_name='カラーコード')
    
    # カスタムマネージャーを使用
    objects = TagManager()
    
    class Meta:
        verbose_name = 'タグ'
        verbose_name_plural = 'タグ'
        ordering = ['-usage_count', 'name']
        # ユーザー内でのタグ名の一意性を保証
        unique_together = ['user', 'name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'usage_count']),
            models.Index(fields=['user', 'name']),
        ]
    
    def __str__(self):
        return f"{self.user.username}:{self.name}"
    
    def increment_usage(self):
        """使用回数をインクリメント"""
        self.usage_count = models.F('usage_count') + 1
        self.save(update_fields=['usage_count'])
        # Refresh from DB to get the actual value
        self.refresh_from_db(fields=['usage_count'])
    
    def get_default_color(self):
        """デフォルトカラーコードを取得"""
        return '#6b7280'  # gray-600
    
    def get_effective_color(self):
        """実際に表示に使用する色を取得（カスタム色 > デフォルト色）"""
        return self.color if self.color else self.get_default_color()
    
    def get_tag_style(self):
        """タグのインラインスタイルを取得"""
        effective_color = self.get_effective_color()
        return f"background-color: {effective_color}; color: white; border-color: {effective_color};"
    
    def get_related_notebooks(self, limit=5):
        """関連ノートブックを取得（同一ユーザーのみ）"""
        return self.notebook_set.filter(
            user=self.user,
            is_public=True
        ).order_by('-updated_at')[:limit]
    
    def get_related_entries(self, limit=5):
        """関連エントリーを取得（同一ユーザーのみ）"""
        return self.entry_set.select_related('notebook').filter(
            notebook__user=self.user
        ).order_by('-created_at')[:limit]
    
    def save(self, *args, **kwargs):
        """保存時に色が未設定の場合はデフォルト色を設定"""
        if not self.color:
            self.color = self.get_default_color()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_or_create_for_user(cls, user, name, **kwargs):
        """ユーザー固有のタグを取得または作成"""
        # #がない場合は自動で追加
        if not name.startswith('#'):
            name = '#' + name
        
        tag, created = cls.objects.get_or_create(
            user=user,
            name=name,
            defaults={
                'description': kwargs.get('description', ''),
                'color': kwargs.get('color', ''),
                'is_active': kwargs.get('is_active', True),
            }
        )
        
        if not created:
            # 既存タグの使用回数をインクリメント
            tag.increment_usage()
        
        return tag, created