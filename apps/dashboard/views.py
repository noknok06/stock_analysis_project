# ========================================
# apps/dashboard/views.py
# ========================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from apps.notes.models import Notebook, Entry
from apps.tags.models import Tag
from apps.dashboard.models import DashboardStats, RecentActivity
from apps.dashboard.services import DashboardService

@login_required
def dashboard_view(request):
    """統合ダッシュボードビュー"""
    try:
        # ダッシュボードサービスを使用して統計を取得
        dashboard_service = DashboardService(request.user)
        context = dashboard_service.get_dashboard_context()
        
        return render(request, 'dashboard/index.html', context)
    
    except Exception as e:
        # エラーハンドリング
        context = {
            'error': 'ダッシュボードの読み込みに失敗しました。',
            'debug_error': str(e) if request.user.is_staff else None
        }
        return render(request, 'dashboard/index.html', context)