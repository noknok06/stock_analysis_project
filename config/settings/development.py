# =================================
# config/settings/development.py - 開発環境（修正版）
# =================================

from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']  # 開発時は * も追加

# 開発環境では SQLite を使用（PostgreSQLが設定されていない場合）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQLを使いたい場合は以下をコメントアウト
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'stock_note',
#         'USER': 'naoki',
#         'PASSWORD': 'XxAaWsz9',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# 開発環境用の追加設定
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# デバッグ用
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# CSRF設定（開発時）
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://3bae-2400-2411-a761-e100-b495-a316-d9ac-2119.ngrok-free.app",
]