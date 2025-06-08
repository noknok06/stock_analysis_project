# ========================================
# apps/notes/management/commands/test_tag_system.py
# ========================================

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.tags.models import Tag
from apps.notes.models import Notebook

class Command(BaseCommand):
    help = 'タグシステムの動作テスト'

    def handle(self, *args, **options):
        try:
            # テストユーザー取得
            user = User.objects.get(username='sample_user')
            
            # テストタグ作成
            test_tags = [
                {'name': '#7203トヨタ', 'category': 'STOCK', 'description': 'トヨタ自動車の銘柄タグ'},
                {'name': '#高配当', 'category': 'STYLE', 'description': '高配当株投資スタイル'},
                {'name': '#長期投資', 'category': 'STRATEGY', 'description': '長期投資戦略'},
                {'name': '#自動車', 'category': 'SECTOR', 'description': '自動車業界セクター'},
                {'name': '#決算分析', 'category': 'ANALYSIS', 'description': '決算分析手法'},
            ]
            
            created_tags = []
            for tag_data in test_tags:
                tag, created = Tag.objects.get_or_create(
                    name=tag_data['name'],
                    defaults={
                        'category': tag_data['category'],
                        'description': tag_data['description'],
                        'usage_count': 1
                    }
                )
                created_tags.append(tag)
                if created:
                    self.stdout.write(f'✓ タグ {tag.name} を作成しました')
                else:
                    self.stdout.write(f'- タグ {tag.name} は既に存在します')
            
            # テストノートブック作成
            notebook, created = Notebook.objects.get_or_create(
                title='タグシステムテスト用ノート',
                user=user,
                defaults={
                    'subtitle': 'タグ機能の動作確認用',
                    'stock_code': '7203',
                    'company_name': 'トヨタ自動車',
                    'investment_reason': 'タグシステムのテスト用ノートです。',
                    'key_points': ['テスト用ポイント1', 'テスト用ポイント2'],
                    'risk_factors': ['テスト用リスク1'],
                    'status': 'ACTIVE'
                }
            )
            
            if created:
                # タグを関連付け
                notebook.tags.set(created_tags)
                self.stdout.write(f'✓ テストノートブック {notebook.title} を作成しました')
                self.stdout.write(f'✓ {len(created_tags)}個のタグを関連付けました')
            else:
                self.stdout.write(f'- テストノートブック {notebook.title} は既に存在します')
            
            # タグ統計表示
            total_tags = Tag.objects.filter(is_active=True).count()
            self.stdout.write(f'\n📊 タグ統計:')
            self.stdout.write(f'- アクティブタグ数: {total_tags}')
            
            # カテゴリ別タグ数
            for category, label in Tag.CATEGORY_CHOICES:
                count = Tag.objects.filter(category=category, is_active=True).count()
                self.stdout.write(f'- {label}: {count}個')
            
            self.stdout.write(
                self.style.SUCCESS('\n✅ タグシステムのテストが完了しました')
            )
            
            # 次のステップを表示
            self.stdout.write('\n🔄 次のテスト手順:')
            self.stdout.write('1. 管理画面でタグを確認: /admin/tags/tag/')
            self.stdout.write('2. ノート作成画面でタグ追加をテスト: /notes/create/')
            self.stdout.write('3. タグ検索APIをテスト: /tags/api/search/')
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('sample_userが見つかりません。先にcreate_sample_dataコマンドを実行してください。')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'エラーが発生しました: {str(e)}')
            )