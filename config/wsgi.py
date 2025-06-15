# =================================
# config/wsgi.py - 更新版
# =================================

import os
from django.core.wsgi import get_wsgi_application

# 本番環境では environment variable で指定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_wsgi_application()