# ========================================
# apps/dashboard/models.py
# ========================================

from django.db import models
from django.contrib.auth.models import User
from apps.common.models import BaseModel

class DashboardStats(BaseModel):
    """ダッシュボード統計情報"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    active_notebooks = models.PositiveIntegerField(default=0, verbose_name='アクティブノート数')
    monthly_entries = models.PositiveIntegerField(default=0, verbose_name='今月のエントリー数')
    total_entries = models.PositiveIntegerField(default=0, verbose_name='総エントリー数')
    goal_achievement_rate = models.FloatField(default=0.0, verbose_name='目標達成率')
    
    class Meta:
        verbose_name = 'ダッシュボード統計'
        verbose_name_plural = 'ダッシュボード統計'
    
    def __str__(self):
        return f"{self.user.username}の統計"


class RecentActivity(BaseModel):
    """最近のアクティビティ"""
    
    ACTIVITY_TYPE_CHOICES = [
        ('NOTEBOOK_CREATED', 'ノート作成'),
        ('ENTRY_ADDED', 'エントリー追加'),
        ('PRICE_ALERT', '価格アラート'),
        ('GOAL_UPDATED', '目標更新'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    activity_type = models.CharField(
        max_length=20, 
        choices=ACTIVITY_TYPE_CHOICES,
        verbose_name='アクティビティタイプ'
    )
    title = models.CharField(max_length=200, verbose_name='タイトル')
    description = models.TextField(blank=True, verbose_name='説明')
    related_object_id = models.UUIDField(null=True, blank=True, verbose_name='関連オブジェクトID')
    
    class Meta:
        verbose_name = '最近のアクティビティ'
        verbose_name_plural = '最近のアクティビティ'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"