# =================================
# config/settings/development.py - 開発環境
# =================================

from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# 開発環境用データベース
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'stock_note',
        'USER': 'naoki',
        'PASSWORD': 'XxAaWsz9',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}