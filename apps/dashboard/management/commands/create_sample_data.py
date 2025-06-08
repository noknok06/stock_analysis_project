from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.tags.models import Tag
from apps.notes.models import Notebook, Entry
from apps.dashboard.models import RecentActivity
import uuid

class Command(BaseCommand):
    help = 'サンプルデータを作成'

    def handle(self, *args, **options):
        # サンプルユーザー作成
        user, created = User.objects.get_or_create(
            username='sample_user',
            defaults={
                'email': 'sample@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(f'ユーザー {user.username} を作成しました')

        # サンプルタグ作成
        sample_tags = [
            {'name': '#7203トヨタ', 'category': 'STOCK'},
            {'name': '#高配当', 'category': 'STYLE'},
            {'name': '#長期投資', 'category': 'STRATEGY'},
            {'name': '#自動車', 'category': 'SECTOR'},
            {'name': '#決算分析', 'category': 'ANALYSIS'},
            {'name': '#業績好調', 'category': 'MARKET'},
            {'name': '#6758ソニー', 'category': 'STOCK'},
            {'name': '#成長株', 'category': 'STYLE'},
            {'name': '#エンタメ', 'category': 'SECTOR'},
        ]

        for tag_data in sample_tags:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={
                    'category': tag_data['category'],
                    'usage_count': 1
                }
            )
            if created:
                self.stdout.write(f'タグ {tag.name} を作成しました')

        # サンプルノートブック作成
        sample_notebooks = [
            {
                'title': '7203 トヨタ自動車',
                'subtitle': '長期保有・配当重視',
                'stock_code': '7203',
                'company_name': 'トヨタ自動車',
                'investment_reason': '安定した配当政策と自動車業界でのリーダーシップ。電動化への取り組みも評価。',
                'target_price': '3,200円',
                'sell_timing': '配当利回り3%を下回った時点',
                'key_points': ['継続的な配当増配', '電動化技術への投資', 'グローバル市場での競争力'],
                'risk_factors': ['為替変動リスク', '電動化競争の激化', '半導体不足の影響'],
                'status': 'ACTIVE'
            },
            {
                'title': '6758 ソニーグループ',
                'subtitle': 'エンタメ・半導体事業分析',
                'stock_code': '6758',
                'company_name': 'ソニーグループ',
                'investment_reason': 'エンターテインメント事業の安定性と半導体事業の成長性を評価。',
                'target_price': '15,000円',
                'sell_timing': 'PER 20倍を超えた時点',
                'key_points': ['PlayStation事業の安定性', '半導体事業の成長', '音楽・映画事業の収益性'],
                'risk_factors': ['ゲーム市場の競争激化', '半導体市場の変動', '為替リスク'],
                'status': 'MONITORING'
            }
        ]

        for notebook_data in sample_notebooks:
            notebook, created = Notebook.objects.get_or_create(
                title=notebook_data['title'],
                user=user,
                defaults=notebook_data
            )
            if created:
                # タグを関連付け
                relevant_tags = Tag.objects.filter(
                    name__in=[f"#{notebook_data['stock_code']}", '#高配当', '#長期投資']
                )
                notebook.tags.set(relevant_tags)
                self.stdout.write(f'ノートブック {notebook.title} を作成しました')

                # サンプルエントリー作成
                sample_entry = Entry.objects.create(
                    notebook=notebook,
                    entry_type='ANALYSIS',
                    title='第3四半期決算分析',
                    content={
                        'summary': f'{notebook_data["company_name"]}の第3四半期決算は好調でした。',
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
                sample_entry.tags.set(relevant_tags)
                self.stdout.write(f'エントリー {sample_entry.title} を作成しました')

        # アクティビティ作成
        RecentActivity.objects.create(
            user=user,
            activity_type='NOTEBOOK_CREATED',
            title='7203 トヨタ自動車 - 新規ノート作成',
            description='長期保有戦略のノートを作成しました'
        )

        self.stdout.write(
            self.style.SUCCESS('サンプルデータの作成が完了しました')
        )