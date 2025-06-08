# ========================================
# apps/common/validators.py
# ========================================

import re
from django.core.exceptions import ValidationError

def validate_stock_code(value):
    """銘柄コードのバリデーション"""
    if not value:
        return
    
    # 日本の銘柄コード（4桁の数字）をチェック
    if not re.match(r'^\d{4}$', value):
        raise ValidationError(
            '銘柄コードは4桁の数字で入力してください（例: 7203）'
        )
    
    # 範囲チェック（実際の銘柄コード範囲）
    code_num = int(value)
    if not (1000 <= code_num <= 9999):
        raise ValidationError(
            '有効な銘柄コードの範囲を入力してください（1000-9999）'
        )

def validate_json_content(value):
    """JSONコンテンツのバリデーション"""
    import json
    try:
        if isinstance(value, str):
            json.loads(value)
    except (json.JSONDecodeError, TypeError):
        raise ValidationError('有効なJSON形式で入力してください')