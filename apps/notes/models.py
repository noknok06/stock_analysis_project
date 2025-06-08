# ========================================
# apps/notes/models.py
# ========================================

import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.common.models import BaseModel
from apps.tags.models import Tag

class Notebook(BaseModel):
    """ノートブック（設計書のノートテーブルに対応）"""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'アクティブ'),
        ('MONITORING', '監視中'),
        ('ATTENTION', '要注意'),
        ('ARCHIVED', 'アーカイブ'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    title = models.CharField(max_length=200, verbose_name='タイトル')
    subtitle = models.CharField(max_length=300, blank=True, verbose_name='サブタイトル')
    stock_code = models.CharField(max_length=10, blank=True, verbose_name='銘柄コード')
    company_name = models.CharField(max_length=100, blank=True, verbose_name='企業名')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE',
        verbose_name='ステータス'
    )
    
    # 投資目標
    target_price = models.CharField(max_length=50, blank=True, verbose_name='目標株価')
    sell_timing = models.TextField(blank=True, verbose_name='売却タイミング')
    investment_reason = models.TextField(verbose_name='投資理由・戦略')
    key_points = models.JSONField(default=list, verbose_name='注目ポイント')
    risk_factors = models.JSONField(default=list, verbose_name='リスク要因')
    
    entry_count = models.PositiveIntegerField(default=0, verbose_name='エントリー数')
    is_public = models.BooleanField(default=False, verbose_name='公開フラグ')
    
    # タグ関連
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='タグ')
    
    class Meta:
        verbose_name = 'ノートブック'
        verbose_name_plural = 'ノートブック'
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title
    
    def get_recent_entries(self, limit=5):
        """最新のエントリーを取得"""
        return self.entries.order_by('-created_at')[:limit]


class Entry(BaseModel):
    """エントリー（設計書のエントリーテーブルに対応）"""
    
    ENTRY_TYPE_CHOICES = [
        ('ANALYSIS', '決算分析'),
        ('NEWS', 'ニュース'),
        ('CALCULATION', '計算結果'),
        ('MEMO', 'メモ'),
        ('GOAL', '投資目標'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notebook = models.ForeignKey(
        Notebook, 
        on_delete=models.CASCADE, 
        related_name='entries',
        verbose_name='ノートブック'
    )
    entry_type = models.CharField(
        max_length=20, 
        choices=ENTRY_TYPE_CHOICES,
        verbose_name='エントリータイプ'
    )
    title = models.CharField(max_length=200, verbose_name='タイトル')
    content = models.JSONField(verbose_name='コンテンツ')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='タグ')
    
    class Meta:
        verbose_name = 'エントリー'
        verbose_name_plural = 'エントリー'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notebook.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        """保存時にノートブックのエントリー数を更新"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.notebook.entry_count += 1
            self.notebook.save(update_fields=['entry_count'])
