from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 認証・アカウント管理
    path('accounts/', include('apps.accounts.urls')),
    
    # メインアプリ
    path('', include('apps.dashboard.urls')),  # ダッシュボードがルート
    path('notes/', include('apps.notes.urls')),  # ノート管理
    path('tags/', include('apps.tags.urls')),   # タグ管理
    
    # API エンドポイント（統合）
    path('api/dashboard/', include('apps.dashboard.api_urls')),
    path('api/notes/', include('apps.notes.api_urls')),
    path('api/tags/', include('apps.tags.api_urls')),
    
    # 外部連携API
    path('api/external/', include('apps.external.urls')),  # 株価データ等
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)