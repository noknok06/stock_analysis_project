# ========================================
# apps/dashboard/services.py
# ========================================

from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from apps.notes.models import Notebook, Entry
from apps.tags.models import Tag
from apps.dashboard.models import RecentActivity

class DashboardService:
    """ダッシュボード関連のビジネスロジック"""
    
    def __init__(self, user):
        self.user = user
    
    def get_dashboard_context(self):
        """ダッシュボード用のコンテキストを取得"""
        current_month = timezone.now().replace(day=1)
        last_30_days = timezone.now() - timedelta(days=30)
        
        # 統計情報
        active_notebooks = Notebook.objects.filter(
            user=self.user,
            status='ACTIVE'
        ).count()
        
        monthly_entries = Entry.objects.filter(
            notebook__user=self.user,
            created_at__gte=current_month
        ).count()
        
        total_entries = Entry.objects.filter(
            notebook__user=self.user
        ).count()
        
        # 最近のアクティビティ
        recent_activities = RecentActivity.objects.filter(
            user=self.user
        )[:5]
        
        # 最新のノート
        recent_notebooks = Notebook.objects.filter(
            user=self.user
        ).order_by('-updated_at')[:5]
        
        # トレンドタグ
        trending_tags = Tag.objects.filter(
            is_active=True
        ).order_by('-usage_count')[:10]
        
        return {
            'stats': {
                'active_notebooks': active_notebooks,
                'monthly_entries': monthly_entries,
                'total_entries': total_entries,
                'goal_achievement_rate': 78.0,  # 仮の値
            },
            'recent_activities': recent_activities,
            'recent_notebooks': recent_notebooks,
            'trending_tags': trending_tags,
        }