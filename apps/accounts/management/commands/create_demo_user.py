# ========================================
# apps/accounts/management/commands/create_demo_user.py
# ========================================

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from apps.accounts.models import UserProfile, UserSettings
from apps.notes.models import Notebook, Entry
from apps.tags.models import Tag

class Command(BaseCommand):
    help = 'デモユーザーとテストアカウントを作成'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=1,
            help='作成するデモユーザー数（デフォルト: 1）'
        )
        parser.add_argument(
            '--with-admin',
            action='store_true',
            help='管理者アカウントも作成する'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='既存ユーザーがいても強制実行'
        )

    def handle(self, *args, **options):
        user_count = options['users']
        with_admin = options['with_admin']
        force = options['force']
        
        try:
            with transaction.atomic():
                created_users = []
                
                # 既存ユーザーチェック
                if not force and User.objects.exists():
                    self.stdout.write(
                        self.style.WARNING(
                            'ユーザーが既に存在します。--force オプションを使用して強制実行してください。'
                        )
                    )
                    return
                
                # 管理者アカウント作成
                if with_admin:
                    admin_user = self.create_admin_user()
                    if admin_user:
                        created_users.append(admin_user)
                
                # デモユーザー作成
                for i in range(user_count):
                    demo_user = self.create_demo_user(i + 1)
                    if demo_user:
                        created_users.append(demo_user)
                
                # 結果表示
                self.stdout.write(
                    self.style.SUCCESS(f'\n✅ {len(created_users)}人のユーザーを作成しました:')
                )
                
                for user in created_users:
                    user_type = '管理者' if user.is_superuser else 'デモユーザー'
                    self.stdout.write(f'  - {user.username} ({user_type})')
                
                # ログイン情報の表示
                self.display_login_info(created_users)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ エラーが発生しました: {str(e)}')
            )

    def create_admin_user(self):
        """管理者ユーザーの作成"""
        try:
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@example.com',
                    'first_name': '管理者',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )
            
            if created:
                admin_user.set_password('admin123456')
                admin_user.save()
                
                # プロフィール設定
                profile = admin_user.userprofile
                profile.display_name = '管理者'
                profile.bio = 'システム管理者アカウント'
                profile.investment_experience = 'EXPERT'
                profile.investment_style = 'MODERATE'
                profile.show_statistics = True
                profile.save()
                
                self.stdout.write(f'✓ 管理者アカウント「{admin_user.username}」を作成しました')
                return admin_user
            else:
                self.stdout.write(f'- 管理者アカウント「{admin_user.username}」は既に存在します')
                return None
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 管理者アカウントの作成に失敗: {str(e)}')
            )
            return None

    def create_demo_user(self, index):
        """デモユーザーの作成"""
        try:
            username = f'demo_user{index}' if index > 1 else 'demo_user'
            email = f'demo{index}@example.com' if index > 1 else 'demo@example.com'
            
            demo_user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'デモ{index}',
                    'last_name': 'ユーザー',
                    'is_active': True,
                }
            )
            
            if created:
                demo_user.set_password('demo123456')
                demo_user.save()
                
                # プロフィール設定
                profile = demo_user.userprofile
                profile.display_name = f'デモユーザー{index}'
                profile.bio = f'これはデモ用のテストアカウント{index}です。投資分析の記録機能をお試しください。'
                
                # バリエーションを持たせた設定
                experiences = ['BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT']
                styles = ['CONSERVATIVE', 'MODERATE', 'AGGRESSIVE', 'SPECULATIVE']
                
                profile.investment_experience = experiences[(index - 1) % len(experiences)]
                profile.investment_style = styles[(index - 1) % len(styles)]
                profile.public_profile = index % 2 == 0  # 偶数番号は公開
                profile.save()
                
                # 設定のカスタマイズ
                settings = demo_user.usersettings
                settings.theme = 'DARK' if index % 2 == 1 else 'LIGHT'
                settings.items_per_page = 12 + (index - 1) * 3
                settings.save()
                
                self.stdout.write(f'✓ デモユーザー「{demo_user.username}」を作成しました')
                return demo_user
            else:
                self.stdout.write(f'- デモユーザー「{demo_user.username}」は既に存在します')
                return None
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ デモユーザー{index}の作成に失敗: {str(e)}')
            )
            return None

    def display_login_info(self, users):
        """ログイン情報の表示"""
        if not users:
            return
            
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📋 ログイン情報'))
        self.stdout.write('='*60)
        
        for user in users:
            user_type = '🔑 管理者' if user.is_superuser else '👤 デモユーザー'
            password = 'admin123456' if user.is_superuser else 'demo123456'
            
            self.stdout.write(f'\n{user_type}')
            self.stdout.write(f'  ユーザー名: {user.username}')
            self.stdout.write(f'  パスワード: {password}')
            self.stdout.write(f'  メール: {user.email}')
            
            try:
                profile = user.userprofile
                self.stdout.write(f'  投資経験: {profile.get_investment_experience_display()}')
                self.stdout.write(f'  投資スタイル: {profile.get_investment_style_display()}')
            except:
                pass
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('🌐 ログインURL: http://localhost:8000/accounts/login/')
        self.stdout.write('⚙️  管理画面: http://localhost:8000/admin/')
        self.stdout.write('='*60)
        
        # 次のステップガイド
        self.stdout.write('\n📝 次のステップ:')
        self.stdout.write('1. python manage.py runserver でサーバーを起動')
        self.stdout.write('2. ブラウザでログインページにアクセス')
        self.stdout.write('3. 上記のアカウント情報でログイン')
        self.stdout.write('4. ノート作成・分析記録機能をお試しください')

    def create_sample_data(self, user):
        """サンプルデータの作成（オプション）"""
        try:
            # サンプルノートブック作成
            notebook = Notebook.objects.create(
                user=user,
                title='7203 トヨタ自動車',
                stock_code='7203',
                company_name='トヨタ自動車',
                investment_reason='安定した配当政策と自動車業界でのリーダーシップを評価',
                target_price='3,200円',
                sell_timing='配当利回り3%を下回った時点',
                key_criteria=['継続的な配当増配', '電動化技術への投資', 'グローバル市場での競争力'],
                risk_factors=['為替変動リスク', '電動化競争の激化', '半導体不足の影響'],
                status='ACTIVE'
            )
            
            # サンプルタグ
            tags = ['#7203トヨタ', '#高配当', '#長期投資', '#自動車']
            for tag_name in tags:
                tag, _ = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'category': 'STOCK' if tag_name.startswith('#7203') else 'STYLE'}
                )
                notebook.tags.add(tag)
            
            # サンプルエントリー
            Entry.objects.create(
                notebook=notebook,
                entry_type='ANALYSIS',
                title='第3四半期決算分析',
                content={
                    'summary': 'トヨタの第3四半期決算は予想を上回る好調な結果となりました。',
                    'key_metrics': {
                        'revenue': '8.7兆円 (+8.2%)',
                        'operating_profit': '2.1兆円 (+12.1%)',
                        'net_income': '1.8兆円 (+15.3%)',
                        'eps': '285円'
                    },
                    'analysis': '売上高は前年同期比で大幅な増加を記録し、営業効率の改善も見られます。',
                    'outlook': '通期予想を上方修正。今後も成長が期待できる状況です。'
                }
            )
            
            self.stdout.write(f'  └ サンプルノート「{notebook.title}」を作成')
            
        except Exception as e:
            self.stdout.write(f'  ⚠️  サンプルデータ作成でエラー: {str(e)}')


# ========================================
# 追加の管理コマンド
# ========================================

class CleanupCommand(BaseCommand):
    """テストデータのクリーンアップ用コマンド"""
    help = 'デモユーザーとテストデータを削除'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='削除を実行することを確認'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  この操作はすべてのデモユーザーとテストデータを削除します。\n'
                    '--confirm オプションを付けて実行してください。'
                )
            )
            return

        try:
            # デモユーザーの削除
            demo_users = User.objects.filter(
                username__startswith='demo'
            )
            admin_users = User.objects.filter(
                username='admin',
                is_superuser=True
            )
            
            deleted_count = 0
            for user in demo_users:
                username = user.username
                user.delete()
                deleted_count += 1
                self.stdout.write(f'✓ {username} を削除しました')
            
            for user in admin_users:
                username = user.username
                user.delete()
                deleted_count += 1
                self.stdout.write(f'✓ {username} を削除しました')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ {deleted_count}人のテストユーザーを削除しました。'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ エラーが発生しました: {str(e)}')
            )