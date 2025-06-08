from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 認証・アカウント管理
    path('accounts/', include('apps.accounts.urls')),
    
    # メインアプリ
    path('', include('apps.dashboard.urls')),
    path('notes/', include('apps.notes.urls')),
    path('tags/', include('apps.tags.urls')),
    
    # API エンドポイント
    path('api/', include('apps.dashboard.urls', namespace='api-dashboard')),
    path('api/notes/', include('apps.notes.urls', namespace='api-notes')),
    path('api/tags/', include('apps.tags.urls', namespace='api-tags')),
]

# 開発環境での静的ファイル配信
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)