# 一時的な解決方法：重複データをクリーンアップするコマンド
# apps/accounts/management/commands/fix_duplicate_profiles.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from apps.accounts.models import UserProfile, UserSettings

class Command(BaseCommand):
    help = '重複したUserProfileとUserSettingsを修正'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際には実行せず、何が修正されるかを表示'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN モード: 実際の修正は行いません')
            )
        
        try:
            with transaction.atomic():
                # 重複プロフィールの確認と修正
                self.fix_duplicate_profiles(dry_run)
                
                # 重複設定の確認と修正
                self.fix_duplicate_settings(dry_run)
                
                # 欠けているプロフィール/設定の作成
                self.create_missing_profiles(dry_run)
                
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS('✅ 重複データの修正が完了しました')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✅ 確認が完了しました。--dry-run を外して実行してください')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ エラーが発生しました: {e}')
            )

    def fix_duplicate_profiles(self, dry_run):
        """重複したUserProfileを修正"""
        self.stdout.write('UserProfileの重複をチェック中...')
        
        # ユーザーごとのプロフィール数をカウント
        from django.db.models import Count
        users_with_multiple_profiles = User.objects.annotate(
            profile_count=Count('userprofile')
        ).filter(profile_count__gt=1)
        
        for user in users_with_multiple_profiles:
            profiles = UserProfile.objects.filter(user=user).order_by('created_at')
            self.stdout.write(f'  ユーザー {user.username}: {profiles.count()}個のプロフィール')
            
            if not dry_run:
                # 最初のプロフィール以外を削除
                profiles_to_delete = profiles[1:]
                for profile in profiles_to_delete:
                    profile.delete()
                    self.stdout.write(f'    削除: プロフィールID {profile.id}')

    def fix_duplicate_settings(self, dry_run):
        """重複したUserSettingsを修正"""
        self.stdout.write('UserSettingsの重複をチェック中...')
        
        # ユーザーごとの設定数をカウント
        from django.db.models import Count
        users_with_multiple_settings = User.objects.annotate(
            settings_count=Count('usersettings')
        ).filter(settings_count__gt=1)
        
        for user in users_with_multiple_settings:
            settings = UserSettings.objects.filter(user=user).order_by('created_at')
            self.stdout.write(f'  ユーザー {user.username}: {settings.count()}個の設定')
            
            if not dry_run:
                # 最初の設定以外を削除
                settings_to_delete = settings[1:]
                for setting in settings_to_delete:
                    setting.delete()
                    self.stdout.write(f'    削除: 設定ID {setting.id}')

    def create_missing_profiles(self, dry_run):
        """欠けているプロフィール/設定を作成"""
        self.stdout.write('欠けているプロフィール/設定をチェック中...')
        
        # プロフィールが無いユーザー
        users_without_profile = User.objects.filter(userprofile__isnull=True)
        for user in users_without_profile:
            self.stdout.write(f'  プロフィール作成: {user.username}')
            if not dry_run:
                UserProfile.objects.create(
                    user=user,
                    display_name=user.first_name or user.username,
                    investment_experience='BEGINNER',
                    investment_style='MODERATE'
                )
        
        # 設定が無いユーザー
        users_without_settings = User.objects.filter(usersettings__isnull=True)
        for user in users_without_settings:
            self.stdout.write(f'  設定作成: {user.username}')
            if not dry_run:
                UserSettings.objects.create(
                    user=user,
                    theme='DARK',
                    language='ja',
                    items_per_page=12
                )
        
        if not users_without_profile and not users_without_settings:
            self.stdout.write('  すべてのユーザーにプロフィールと設定が存在します')


# 簡単な修正スクリプト（manage.py shell で実行）
class QuickFix:
    """
    manage.py shell で以下を実行:
    
    from apps.accounts.management.commands.fix_duplicate_profiles import QuickFix
    QuickFix.fix_all()
    """
    
    @staticmethod
    def fix_all():
        from django.contrib.auth.models import User
        from apps.accounts.models import UserProfile, UserSettings
        from django.db import transaction
        
        print("重複データの修正を開始...")
        
        try:
            with transaction.atomic():
                # 重複プロフィール削除
                for user in User.objects.all():
                    profiles = UserProfile.objects.filter(user=user)
                    if profiles.count() > 1:
                        print(f"ユーザー {user.username}: {profiles.count()}個の重複プロフィールを修正")
                        # 最初以外を削除
                        profiles.exclude(id=profiles.first().id).delete()
                
                # 重複設定削除  
                for user in User.objects.all():
                    settings = UserSettings.objects.filter(user=user)
                    if settings.count() > 1:
                        print(f"ユーザー {user.username}: {settings.count()}個の重複設定を修正")
                        # 最初以外を削除
                        settings.exclude(id=settings.first().id).delete()
                
                # 欠けているものを作成
                for user in User.objects.all():
                    profile, created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={'display_name': user.username}
                    )
                    if created:
                        print(f"ユーザー {user.username}: プロフィールを作成")
                    
                    settings, created = UserSettings.objects.get_or_create(
                        user=user,
                        defaults={'theme': 'DARK', 'language': 'ja'}
                    )
                    if created:
                        print(f"ユーザー {user.username}: 設定を作成")
                
                print("✅ 修正完了")
                
        except Exception as e:
            print(f"❌ エラー: {e}")