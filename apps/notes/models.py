# ========================================
# apps/notes/models.py - 新しいノート構成
# ========================================

import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.common.models import BaseModel
from apps.tags.models import Tag

class Notebook(BaseModel):
    """ノートブック（テーマ・カテゴリ単位）"""
    
    NOTEBOOK_TYPE_CHOICES = [
        ('THEME', 'テーマ型'),  # 複数銘柄をテーマでまとめる
        ('WATCHLIST', 'ウォッチリスト'),  # 監視銘柄リスト
        ('PORTFOLIO', 'ポートフォリオ'),  # 実際の保有銘柄
        ('RESEARCH', 'リサーチ'),  # 分析・調査用
        ('SECTOR', 'セクター分析'),  # 業界・セクター分析
        ('EVENT', 'イベント追跡'),  # 決算・IRなどイベント追跡
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'アクティブ'),
        ('MONITORING', '監視中'),
        ('ARCHIVED', 'アーカイブ'),
        ('COMPLETED', '完了'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    
    # 基本情報
    title = models.CharField(max_length=200, verbose_name='ノートタイトル')
    subtitle = models.CharField(max_length=300, blank=True, verbose_name='サブタイトル')
    description = models.TextField(blank=True, verbose_name='説明')
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
    
    # メタ情報
    objectives = models.JSONField(default=list, verbose_name='目的・目標')  # ["長期投資", "配当重視"]
    key_themes = models.JSONField(default=list, verbose_name='キーテーマ')  # ["脱炭素", "DX"]
    notes = models.TextField(blank=True, verbose_name='ノート全体のメモ')
    
    # 統計情報
    entry_count = models.PositiveIntegerField(default=0, verbose_name='エントリー数')
    stock_count = models.PositiveIntegerField(default=0, verbose_name='銘柄数')
    last_entry_date = models.DateTimeField(null=True, blank=True, verbose_name='最終エントリー日')
    
    # 公開設定
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
    
    def get_stock_list(self):
        """このノートに含まれる銘柄一覧を取得"""
        return self.entries.exclude(stock_code='').values(
            'stock_code', 'company_name'
        ).distinct()
    
    def update_statistics(self):
        """統計情報を更新"""
        self.entry_count = self.entries.count()
        self.stock_count = self.entries.exclude(stock_code='').values('stock_code').distinct().count()
        latest_entry = self.entries.order_by('-created_at').first()
        self.last_entry_date = latest_entry.created_at if latest_entry else None
        self.save(update_fields=['entry_count', 'stock_count', 'last_entry_date'])


class SubNotebook(BaseModel):
    """サブノート（章立て・カテゴリ小分け）"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notebook = models.ForeignKey(
        Notebook, 
        on_delete=models.CASCADE, 
        related_name='sub_notebooks',
        verbose_name='親ノートブック'
    )
    
    title = models.CharField(max_length=100, verbose_name='サブノートタイトル')
    description = models.TextField(blank=True, verbose_name='説明')
    order_index = models.PositiveIntegerField(default=0, verbose_name='表示順序')
    
    # 統計情報
    entry_count = models.PositiveIntegerField(default=0, verbose_name='エントリー数')
    
    class Meta:
        verbose_name = 'サブノート'
        verbose_name_plural = 'サブノート'
        ordering = ['order_index', 'created_at']
        unique_together = ['notebook', 'title']
    
    def __str__(self):
        return f"{self.notebook.title} - {self.title}"


class Entry(BaseModel):
    """エントリー（個別銘柄・イベント記録）"""
    
    ENTRY_TYPE_CHOICES = [
        ('STOCK_ANALYSIS', '銘柄分析'),
        ('EARNINGS', '決算分析'),
        ('NEWS_EVENT', 'ニュース・イベント'),
        ('VALUATION', 'バリュエーション'),
        ('TECHNICAL', 'テクニカル分析'),
        ('MEMO', 'メモ・気づき'),
        ('GOAL_SETTING', '目標設定'),
        ('PORTFOLIO_UPDATE', 'ポートフォリオ更新'),
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
        null=True,
        blank=True,
        related_name='entries',
        verbose_name='サブノート'
    )
    
    # 基本情報
    title = models.CharField(max_length=200, verbose_name='エントリータイトル')
    entry_type = models.CharField(
        max_length=20, 
        choices=ENTRY_TYPE_CHOICES,
        verbose_name='エントリータイプ'
    )
    
    # 銘柄情報（個別銘柄エントリーの場合）
    stock_code = models.CharField(max_length=10, blank=True, verbose_name='銘柄コード')
    company_name = models.CharField(max_length=100, blank=True, verbose_name='企業名')
    market = models.CharField(max_length=50, blank=True, verbose_name='市場')  # 東証プライム、NASDAQ等
    
    # イベント情報（イベント系エントリーの場合）
    event_date = models.DateField(null=True, blank=True, verbose_name='イベント日')
    event_type = models.CharField(max_length=50, blank=True, verbose_name='イベント種別')  # 決算発表、株主総会等
    
    # コンテンツ
    content = models.JSONField(verbose_name='コンテンツ')
    summary = models.TextField(blank=True, verbose_name='サマリー')  # 検索用の平文サマリー
    
    # 数値データ（分析結果等）
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='現在株価')
    target_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='目標株価')
    rating = models.CharField(max_length=20, blank=True, verbose_name='投資判定')  # 買い、売り、中立等
    
    # ブックマーク・重要度
    is_bookmarked = models.BooleanField(default=False, verbose_name='ブックマーク')
    importance = models.IntegerField(default=1, choices=[(i, f'{i}') for i in range(1, 6)], verbose_name='重要度')
    
    # タグ
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='タグ')
    
    class Meta:
        verbose_name = 'エントリー'
        verbose_name_plural = 'エントリー'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stock_code']),
            models.Index(fields=['entry_type']),
            models.Index(fields=['event_date']),
            models.Index(fields=['is_bookmarked']),
        ]
    
    def __str__(self):
        if self.stock_code:
            return f"{self.stock_code} {self.company_name} - {self.title}"
        return self.title
    
    def save(self, *args, **kwargs):
        """保存時にノートブックの統計を更新"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.notebook.update_statistics()
            if self.sub_notebook:
                self.sub_notebook.entry_count += 1
                self.sub_notebook.save(update_fields=['entry_count'])
    
    def get_display_name(self):
        """表示用の名前を取得"""
        if self.stock_code and self.company_name:
            return f"{self.stock_code} {self.company_name}"
        return self.title


class EntryRelation(BaseModel):
    """エントリー間の関連性"""
    
    RELATION_TYPE_CHOICES = [
        ('FOLLOW_UP', 'フォローアップ'),
        ('COMPARISON', '比較対象'),
        ('REFERENCE', '参考'),
        ('CONTRADICTION', '矛盾・見直し'),
        ('UPDATE', '更新・修正'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_entry = models.ForeignKey(
        Entry, 
        on_delete=models.CASCADE, 
        related_name='related_from',
        verbose_name='関連元エントリー'
    )
    to_entry = models.ForeignKey(
        Entry, 
        on_delete=models.CASCADE, 
        related_name='related_to',
        verbose_name='関連先エントリー'
    )
    relation_type = models.CharField(
        max_length=20, 
        choices=RELATION_TYPE_CHOICES,
        verbose_name='関連タイプ'
    )
    notes = models.TextField(blank=True, verbose_name='関連についてのメモ')
    
    class Meta:
        verbose_name = 'エントリー関連'
        verbose_name_plural = 'エントリー関連'
        unique_together = ['from_entry', 'to_entry', 'relation_type']
    
    def __str__(self):
        return f"{self.from_entry.title} -> {self.to_entry.title} ({self.get_relation_type_display()})"