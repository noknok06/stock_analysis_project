from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.common.models import BaseModel

class TagManager(models.Manager):
    """タグマネージャー（カスタムクエリセット）"""
    
    def get_trending_tags(self, limit=10):
        """トレンドタグを取得（使用頻度とアクティビティベース）"""
        # 過去30日間でアクティブなタグを優先
        recent_threshold = timezone.now() - timedelta(days=30)
        
        return self.filter(
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
    
    def get_popular_tags(self, limit=20):
        """人気タグを取得（総使用回数ベース）"""
        return self.filter(
            is_active=True,
            usage_count__gt=0
        ).order_by('-usage_count', '-updated_at')[:limit]
    
    def get_tags_by_category(self, category, limit=10):
        """カテゴリー別タグを取得"""
        return self.filter(
            category=category,
            is_active=True,
            usage_count__gt=0
        ).order_by('-usage_count', '-updated_at')[:limit]
    
    def search_tags(self, query):
        """タグを検索"""
        if not query:
            return self.none()
        
        return self.filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query),
            is_active=True
        ).order_by('-usage_count', 'name')


class Tag(BaseModel):
    """タグモデル（既存のモデルを拡張）"""
    
    CATEGORY_CHOICES = [
        ('STOCK', '銘柄'),
        ('SECTOR', 'セクター'),
        ('STRATEGY', '投資戦略'),
        ('ANALYSIS', '分析手法'),
        ('MARKET', '市場'),
        ('RISK', 'リスク'),
        ('EVENT', 'イベント'),
        ('OTHER', 'その他'),
    ]
    
    name = models.CharField(max_length=50, unique=True, verbose_name='タグ名')
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='OTHER',
        verbose_name='カテゴリ'
    )
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
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['usage_count']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name
    
    def increment_usage(self):
        """使用回数をインクリメント"""
        self.usage_count = models.F('usage_count') + 1
        self.save(update_fields=['usage_count'])
        # Refresh from DB to get the actual value
        self.refresh_from_db(fields=['usage_count'])
    
    def get_color_class(self):
        """カテゴリに基づくCSSクラスを取得"""
        color_map = {
            'STOCK': 'bg-red-600',
            'SECTOR': 'bg-green-600', 
            'STRATEGY': 'bg-blue-600',
            'ANALYSIS': 'bg-orange-600',
            'MARKET': 'bg-purple-600',
            'RISK': 'bg-yellow-600',
            'EVENT': 'bg-indigo-600',
            'OTHER': 'bg-gray-600',
        }
        return color_map.get(self.category, 'bg-gray-600')
    
    def get_related_notebooks(self, limit=5):
        """関連ノートブックを取得"""
        return self.notebook_set.filter(
            is_public=True
        ).order_by('-updated_at')[:limit]
    
    def get_related_entries(self, limit=5):
        """関連エントリーを取得"""
        return self.entry_set.select_related('notebook').order_by('-created_at')[:limit]