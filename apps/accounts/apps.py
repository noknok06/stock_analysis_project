# ========================================
# apps/accounts/apps.py
# ========================================

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'アカウント管理'
    
    def ready(self):
        """アプリ起動時の初期化処理"""
        import apps.accounts.signals