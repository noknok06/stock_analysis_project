# ========================================
# apps/accounts/signals.py
# ========================================

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile, UserSettings


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """ユーザー作成時にプロフィールとセッティングを自動作成"""
    if created:
        # プロフィール作成
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                'display_name': instance.first_name or instance.username,
                'investment_experience': 'BEGINNER',
                'investment_style': 'MODERATE',
                'email_notifications': True,
                'public_profile': False,
                'show_statistics': True,
            }
        )
        
        # セッティング作成
        UserSettings.objects.get_or_create(
            user=instance,
            defaults={
                'theme': 'DARK',
                'language': 'ja',
                'items_per_page': 12,
                'show_recent_activity': True,
                'show_trending_tags': True,
                'show_statistics': True,
                'price_alert_enabled': True,
                'news_notification_enabled': True,
            }
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """ユーザー保存時にプロフィールも保存"""
    try:
        # プロフィールが存在する場合のみ保存
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()
        if hasattr(instance, 'usersettings'):
            instance.usersettings.save()
    except (UserProfile.DoesNotExist, UserSettings.DoesNotExist):
        # プロフィールが存在しない場合は作成
        create_user_profile(sender, instance, created=True)


@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """ユーザー削除時の関連データクリーンアップ"""
    try:
        # 関連するノートブックやエントリーは外部キー制約で自動削除される
        # ここでは追加のクリーンアップ処理を記述
        
        # ログイン履歴の削除（設定に応じて）
        from apps.accounts.models import LoginHistory
        LoginHistory.objects.filter(user=instance).delete()
        
        # ダッシュボード統計の削除
        from apps.dashboard.models import DashboardStats, RecentActivity
        DashboardStats.objects.filter(user=instance).delete()
        RecentActivity.objects.filter(user=instance).delete()
        
    except Exception as e:
        # エラーログを記録（実際の環境では適切なロギングを使用）
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"ユーザー削除時のクリーンアップエラー: {e}", exc_info=True)


# ========================================
# ノートブック・エントリー作成時の統計更新
# ========================================

from apps.notes.models import Notebook, Entry

@receiver(post_save, sender=Notebook)
def update_notebook_statistics(sender, instance, created, **kwargs):
    """ノートブック作成・更新時の統計情報更新"""
    if created:
        try:
            profile = instance.user.userprofile
            profile.update_statistics()
        except UserProfile.DoesNotExist:
            pass


@receiver(post_save, sender=Entry)
def update_entry_statistics(sender, instance, created, **kwargs):
    """エントリー作成・更新時の統計情報更新"""
    if created:
        try:
            profile = instance.notebook.user.userprofile
            profile.update_statistics()
        except UserProfile.DoesNotExist:
            pass


@receiver(post_delete, sender=Notebook)
def update_notebook_statistics_on_delete(sender, instance, **kwargs):
    """ノートブック削除時の統計情報更新"""
    try:
        profile = instance.user.userprofile
        profile.update_statistics()
    except UserProfile.DoesNotExist:
        pass


@receiver(post_delete, sender=Entry)
def update_entry_statistics_on_delete(sender, instance, **kwargs):
    """エントリー削除時の統計情報更新"""
    try:
        profile = instance.notebook.user.userprofile
        profile.update_statistics()
    except UserProfile.DoesNotExist:
        pass


# ========================================
# ダッシュボードアクティビティ記録
# ========================================

@receiver(post_save, sender=Notebook)
def record_notebook_activity(sender, instance, created, **kwargs):
    """ノートブック作成時のアクティビティ記録"""
    if created:
        try:
            from apps.dashboard.models import RecentActivity
            RecentActivity.objects.create(
                user=instance.user,
                activity_type='NOTEBOOK_CREATED',
                title=f'{instance.title} - 新規ノート作成',
                description=f'銘柄: {instance.company_name or instance.stock_code or "未設定"}',
                related_object_id=instance.id
            )
        except Exception:
            # エラーが発生してもメイン処理に影響しないよう
            pass


@receiver(post_save, sender=Entry)
def record_entry_activity(sender, instance, created, **kwargs):
    """エントリー作成時のアクティビティ記録"""
    if created:
        try:
            from apps.dashboard.models import RecentActivity
            RecentActivity.objects.create(
                user=instance.notebook.user,
                activity_type='ENTRY_ADDED',
                title=f'{instance.notebook.title} - エントリー追加',
                description=f'{instance.get_entry_type_display()}: {instance.title}',
                related_object_id=instance.id
            )
        except Exception:
            # エラーが発生してもメイン処理に影響しないよう
            pass