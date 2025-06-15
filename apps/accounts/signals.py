# apps/accounts/signals.py を修正

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import IntegrityError
from apps.accounts.models import UserProfile, UserSettings
from apps.notes.models import Notebook, Entry
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """ユーザー作成時にプロフィールとセッティングを自動作成（修正版）"""
    if created:
        try:
            # プロフィール作成（get_or_createで重複を防ぐ）
            profile, profile_created = UserProfile.objects.get_or_create(
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
            
            if profile_created:
                logger.info(f"UserProfile created for user {instance.username}")
            else:
                logger.info(f"UserProfile already exists for user {instance.username}")
            
            # セッティング作成（get_or_createで重複を防ぐ）
            settings, settings_created = UserSettings.objects.get_or_create(
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
            
            if settings_created:
                logger.info(f"UserSettings created for user {instance.username}")
            else:
                logger.info(f"UserSettings already exists for user {instance.username}")
                
        except IntegrityError as e:
            logger.error(f"IntegrityError in create_user_profile for user {instance.username}: {e}")
            # 既に存在する場合は無視
            pass
        except Exception as e:
            logger.error(f"Unexpected error in create_user_profile for user {instance.username}: {e}", exc_info=True)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """ユーザー保存時にプロフィールも保存（修正版）"""
    try:
        # プロフィールが存在する場合のみ保存
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()
        else:
            # プロフィールが存在しない場合は作成を試行
            logger.warning(f"UserProfile not found for user {instance.username}, attempting to create")
            create_user_profile(sender, instance, created=True)
            
        if hasattr(instance, 'usersettings'):
            instance.usersettings.save()
        else:
            # セッティングが存在しない場合は作成を試行
            logger.warning(f"UserSettings not found for user {instance.username}, attempting to create")
            create_user_profile(sender, instance, created=True)
            
    except (UserProfile.DoesNotExist, UserSettings.DoesNotExist):
        # プロフィールが存在しない場合は作成
        logger.info(f"Creating missing profile/settings for user {instance.username}")
        create_user_profile(sender, instance, created=True)
    except Exception as e:
        logger.error(f"Error in save_user_profile for user {instance.username}: {e}", exc_info=True)


@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """ユーザー削除時の関連データクリーンアップ"""
    try:
        # 関連するノートブックやエントリーは外部キー制約で自動削除される
        # ここでは追加のクリーンアップ処理を記述
        
        # ログイン履歴の削除（設定に応じて）
        from apps.accounts.models import LoginHistory
        LoginHistory.objects.filter(user=instance).delete()
        
        # ダッシュボード統計の削除（アプリが存在する場合）
        try:
            from apps.dashboard.models import DashboardStats, RecentActivity
            DashboardStats.objects.filter(user=instance).delete()
            RecentActivity.objects.filter(user=instance).delete()
        except ImportError:
            # ダッシュボードアプリが存在しない場合は無視
            pass
        
        logger.info(f"Cleanup completed for user {instance.username}")
        
    except Exception as e:
        # エラーログを記録（実際の環境では適切なロギングを使用）
        logger.error(f"ユーザー削除時のクリーンアップエラー for {instance.username}: {e}", exc_info=True)


# ========================================
# ノートブック・エントリー作成時の統計更新
# ========================================

@receiver(post_save, sender=Notebook)
def update_notebook_statistics(sender, instance, created, **kwargs):
    """ノートブック作成・更新時の統計情報更新"""
    if created:
        try:
            profile, profile_created = UserProfile.objects.get_or_create(user=instance.user)
            profile.update_statistics()
        except Exception as e:
            logger.error(f"Error updating notebook statistics for user {instance.user.username}: {e}")


@receiver(post_save, sender=Entry)
def update_entry_statistics(sender, instance, created, **kwargs):
    """エントリー作成・更新時の統計情報更新"""
    if created:
        try:
            profile, profile_created = UserProfile.objects.get_or_create(user=instance.notebook.user)
            profile.update_statistics()
        except Exception as e:
            logger.error(f"Error updating entry statistics for user {instance.notebook.user.username}: {e}")


@receiver(post_delete, sender=Notebook)
def update_notebook_statistics_on_delete(sender, instance, **kwargs):
    """ノートブック削除時の統計情報更新"""
    try:
        profile, profile_created = UserProfile.objects.get_or_create(user=instance.user)
        profile.update_statistics()
    except Exception as e:
        logger.error(f"Error updating notebook statistics on delete for user {instance.user.username}: {e}")


@receiver(post_delete, sender=Entry)
def update_entry_statistics_on_delete(sender, instance, **kwargs):
    """エントリー削除時の統計情報更新"""
    try:
        profile, profile_created = UserProfile.objects.get_or_create(user=instance.notebook.user)
        profile.update_statistics()
    except Exception as e:
        logger.error(f"Error updating entry statistics on delete for user {instance.notebook.user.username}: {e}")


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
        except ImportError:
            # ダッシュボードアプリが存在しない場合は無視
            pass
        except Exception as e:
            # エラーが発生してもメイン処理に影響しないよう
            logger.error(f"Error recording notebook activity: {e}")


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
        except ImportError:
            # ダッシュボードアプリが存在しない場合は無視
            pass
        except Exception as e:
            # エラーが発生してもメイン処理に影響しないよう
            logger.error(f"Error recording entry activity: {e}")