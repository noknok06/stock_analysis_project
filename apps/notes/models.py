# ========================================
# apps/notes/models.py - 簡素化版
# ========================================

import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.common.models import BaseModel
from apps.tags.models import Tag
from django.db.models import Count, Q

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
    
    # 選定基準とリスク要因のみ残す
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
    
    def save(self, *args, **kwargs):
        """保存時にエントリー数を更新"""
        super().save(*args, **kwargs)
        self.update_entry_count()
    
    def update_entry_count(self):
        """エントリー数を正確にカウントして更新"""
        actual_count = self.entries.count()
        if self.entry_count != actual_count:
            self.entry_count = actual_count
            super(Notebook, self).save(update_fields=['entry_count'])
    
    def get_recent_entries(self, limit=5):
        """最新のエントリーを取得"""
        return self.entries.order_by('-created_at')[:limit]
    
    def get_stock_count(self):
        """ノート内の銘柄数を取得"""
        return self.entries.exclude(
            Q(stock_code='') | Q(stock_code__isnull=True)
        ).values('stock_code').distinct().count()
    
    def get_stocks_list(self):
        """ノート内の銘柄一覧を取得"""
        return self.entries.exclude(
            Q(stock_code='') | Q(stock_code__isnull=True)
        ).values('stock_code', 'company_name').distinct().order_by('stock_code')
    
    def get_important_entries_count(self):
        """重要エントリー数を取得"""
        return self.entries.filter(is_important=True).count()
    
    def get_recent_entries_count(self, days=7):
        """最近のエントリー数を取得"""
        from django.utils import timezone
        from datetime import timedelta
        since_date = timezone.now() - timedelta(days=days)
        return self.entries.filter(created_at__gte=since_date).count()
    
    def get_bookmarked_entries_count(self):
        """ブックマーク済みエントリー数を取得"""
        return self.entries.filter(is_bookmarked=True).count()


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
    
    def get_entries_count(self):
        """このサブノートのエントリー数を取得"""
        return self.entries.count()


class Entry(BaseModel):
    """エントリー（1銘柄 or 1イベント単位）"""
    
    ENTRY_TYPE_CHOICES = [
        ('ANALYSIS', '決算分析'),
        ('NEWS', 'ニュース'),
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
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new:
            self.notebook.update_entry_count()
    
    def delete(self, *args, **kwargs):
        """削除時にノートブックのエントリー数を更新"""
        notebook = self.notebook
        super().delete(*args, **kwargs)
        notebook.update_entry_count()
    
    def get_stock_display(self):
        """銘柄表示用"""
        if self.stock_code and self.company_name:
            return f"{self.stock_code} {self.company_name}"
        elif self.stock_code:
            return self.stock_code
        elif self.company_name:
            return self.company_name
        return "銘柄未設定"
    
    def get_content_preview(self, max_length=100):
        """コンテンツプレビューを取得"""
        if not self.content:
            return "コンテンツなし"
        
        # エントリータイプに応じてプレビューテキストを生成
        if self.entry_type == 'ANALYSIS' and self.content.get('summary'):
            text = self.content['summary']
        elif self.entry_type == 'NEWS' and self.content.get('headline'):
            text = self.content['headline']
        elif self.entry_type == 'MEMO' and self.content.get('observation'):
            text = self.content['observation']
        elif self.entry_type == 'GOAL' and self.content.get('target_price'):
            text = f"目標株価: {self.content['target_price']}"
        else:
            # その他の場合は最初の値を取得
            values = [v for v in self.content.values() if isinstance(v, str) and v.strip()]
            text = values[0] if values else "詳細はクリックして確認"
        
        return text[:max_length] + '...' if len(text) > max_length else text
    
    def has_stock_info(self):
        """銘柄情報があるかどうか"""
        return bool(self.stock_code or self.company_name)


# シグナルを使用してエントリー数の整合性を保つ
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Entry)
def update_notebook_entry_count_on_save(sender, instance, created, **kwargs):
    """エントリー保存時にノートブックのエントリー数を更新"""
    if created:
        instance.notebook.update_entry_count()

@receiver(post_delete, sender=Entry)
def update_notebook_entry_count_on_delete(sender, instance, **kwargs):
    """エントリー削除時にノートブックのエントリー数を更新"""
    try:
        instance.notebook.update_entry_count()
    except Notebook.DoesNotExist:
        pass