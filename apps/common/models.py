# ========================================
# apps/common/models.py
# ========================================

from django.db import models
from django.contrib.auth.models import User

class BaseModel(models.Model):
    """全モデルの基底クラス"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        abstract = True
