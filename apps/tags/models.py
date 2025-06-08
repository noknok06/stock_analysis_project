# ========================================
# apps/tags/models.py
# ========================================

from django.db import models
from apps.common.models import BaseModel

class Tag(BaseModel):
    """統一タグシステム"""
    
    # タグカテゴリ選択肢
    CATEGORY_CHOICES = [
        ('STOCK', '銘柄'),
        ('STYLE', '投資スタイル'),
        ('SECTOR', '業界セクター'),
        ('ANALYSIS', '分析手法'),
        ('STRATEGY', '投資戦略'),
        ('MARKET', '市場状況'),
        ('RISK', 'リスク要因'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name='タグ名')
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        verbose_name='カテゴリ'
    )
    description = models.TextField(blank=True, verbose_name='説明')
    usage_count = models.PositiveIntegerField(default=0, verbose_name='使用回数')
    is_active = models.BooleanField(default=True, verbose_name='有効フラグ')
    
    class Meta:
        verbose_name = 'タグ'
        verbose_name_plural = 'タグ'
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return f"#{self.name}"
    
    def increment_usage(self):
        """使用回数をインクリメント"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])