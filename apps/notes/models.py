# ========================================
# apps/notes/models.py - 見直し版
# ========================================

import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.common.models import BaseModel
from apps.tags.models import Tag

class Notebook(BaseModel):
    """ノートブック（テーマ単位のフォルダ的役割）"""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'アクティブ'),
        ('MONITORING', '監視中'),
        ('ATTENTION', '要注意'),
        ('ARCHIVED', 'アーカイブ'),
    ]
    
    NOTEBOOK_TYPE_CHOICES = [
        ('THEME', 'テーマ型（複数銘柄）'),
        ('STOCK_FOCUSED', '銘柄特化型（1銘柄集中）'),
        ('PORTFOLIO', 'ポートフォリオ管理'),
        ('RESEARCH', '調査・研究'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    title = models.CharField(max_length=200, verbose_name='ノートタイトル')
    subtitle = models.CharField(max_length=300, blank=True, verbose_name='サブタイトル')
    description = models.TextField(blank=True, verbose_name='ノートの説明')
    notebook_type = models.CharField(
        max_length=20, 
        choices=NOTEBOOK_TYPE_CHOICES, 
        default='THEME',
        verbose_name='ノートタイプ'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE',
        verbose_name='ステータス'
    )
    
    # 投資テーマ・目標（テーマ全体の戦略）
    investment_strategy = models.TextField(blank=True, verbose_name='投資戦略・テーマ')
    target_allocation = models.CharField(max_length=100, blank=True, verbose_name='目標配分')
    key_criteria = models.JSONField(default=list, verbose_name='選定基準')
    risk_factors = models.JSONField(default=list, verbose_name='リスク要因')
    
    entry_count = models.PositiveIntegerField(default=0, verbose_name='エントリー数')
    is_public = models.BooleanField(default=False, verbose_name='公開フラグ')
    is_favorite = models.BooleanField(default=False, verbose_name='お気に入り')
    
    # タグ関連
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='タグ')
    
    class Meta:
        verbose_name = 'ノートブック'
        verbose_name_plural = 'ノートブック'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['notebook_type']),
            models.Index(fields=['is_favorite']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_recent_entries(self, limit=5):
        """最新のエントリーを取得"""
        return self.entries.order_by('-created_at')[:limit]
    
    def get_stock_count(self):
        """ノート内の銘柄数を取得"""
        return self.entries.exclude(stock_code='').values('stock_code').distinct().count()
    
    def get_stocks_list(self):
        """ノート内の銘柄一覧を取得"""
        return self.entries.exclude(stock_code='').values('stock_code', 'company_name').distinct()


class SubNotebook(BaseModel):
    """サブノート（章立て・カテゴリ分け用）"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notebook = models.ForeignKey(
        Notebook, 
        on_delete=models.CASCADE, 
        related_name='sub_notebooks',
        verbose_name='親ノートブック'
    )
    title = models.CharField(max_length=200, verbose_name='サブノートタイトル')
    description = models.TextField(blank=True, verbose_name='説明')
    order = models.PositiveIntegerField(default=0, verbose_name='表示順')
    
    class Meta:
        verbose_name = 'サブノート'
        verbose_name_plural = 'サブノート'
        ordering = ['order', 'created_at']
        unique_together = ['notebook', 'title']
    
    def __str__(self):
        return f"{self.notebook.title} - {self.title}"


class Entry(BaseModel):
    """エントリー（1銘柄 or 1イベント単位）"""
    
    ENTRY_TYPE_CHOICES = [
        ('ANALYSIS', '決算分析'),
        ('NEWS', 'ニュース'),
        ('CALCULATION', '計算結果'),
        ('MEMO', 'メモ'),
        ('GOAL', '投資目標'),
        ('EARNINGS', '決算発表'),
        ('IR_EVENT', 'IRイベント'),
        ('MARKET_EVENT', '市場イベント'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notebook = models.ForeignKey(
        Notebook, 
        on_delete=models.CASCADE, 
        related_name='entries',
        verbose_name='ノートブック'
    )
    sub_notebook = models.ForeignKey(
        SubNotebook, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='entries',
        verbose_name='サブノート'
    )
    
    # エントリー基本情報
    entry_type = models.CharField(
        max_length=20, 
        choices=ENTRY_TYPE_CHOICES,
        verbose_name='エントリータイプ'
    )
    title = models.CharField(max_length=200, verbose_name='エントリータイトル')
    content = models.JSONField(verbose_name='コンテンツ')
    
    # 銘柄情報（エントリーレベルで管理）
    stock_code = models.CharField(max_length=10, blank=True, verbose_name='銘柄コード')
    company_name = models.CharField(max_length=100, blank=True, verbose_name='企業名')
    market = models.CharField(max_length=20, blank=True, verbose_name='市場')
    
    # イベント情報
    event_date = models.DateField(null=True, blank=True, verbose_name='イベント日')
    is_important = models.BooleanField(default=False, verbose_name='重要フラグ')
    is_bookmarked = models.BooleanField(default=False, verbose_name='ブックマーク')
    
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='タグ')
    
    class Meta:
        verbose_name = 'エントリー'
        verbose_name_plural = 'エントリー'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notebook', 'stock_code']),
            models.Index(fields=['entry_type', 'event_date']),
            models.Index(fields=['is_important']),
            models.Index(fields=['is_bookmarked']),
        ]
    
    def __str__(self):
        return f"{self.notebook.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        """保存時にノートブックのエントリー数を更新"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.notebook.entry_count += 1
            self.notebook.save(update_fields=['entry_count'])
    
    def get_stock_display(self):
        """銘柄表示用"""
        if self.stock_code and self.company_name:
            return f"{self.stock_code} {self.company_name}"
        elif self.stock_code:
            return self.stock_code
        elif self.company_name:
            return self.company_name
        return "銘柄未設定"

