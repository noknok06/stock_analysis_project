# =================================
# deploy.sh - 簡単なデプロイスクリプト
# =================================

#!/bin/bash

echo "🚀 Starting deployment..."

# 本番環境設定
export DJANGO_SETTINGS_MODULE=config.settings.production

# 依存関係インストール
pip install -r requirements.txt

# マイグレーション
python manage.py migrate

# 静的ファイル収集
python manage.py collectstatic --noinput

echo "✅ Deployment completed!"