from django.core.management.base import BaseCommand
from apps.tags.models import Tag

class Command(BaseCommand):
    """タグのメンテナンスコマンド"""
    help = 'タグのメンテナンス処理を実行'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='使用されていないタグを無効化',
        )
        parser.add_argument(
            '--update-colors',
            action='store_true',
            help='タグの色を自動設定',
        )
    
    def handle(self, *args, **options):
        if options['cleanup']:
            self.cleanup_unused_tags()
        
        if options['update_colors']:
            self.update_tag_colors()
    
    def cleanup_unused_tags(self):
        """使用されていないタグを無効化"""
        unused_tags = Tag.objects.filter(
            usage_count=0,
            is_active=True
        )
        
        count = unused_tags.update(is_active=False)
        self.stdout.write(
            self.style.SUCCESS(f'{count}個の未使用タグを無効化しました')
        )
    
    def update_tag_colors(self):
        """タグのカテゴリに基づいて色を自動設定"""
        color_map = {
            'STOCK': '#ef4444',    # red
            'SECTOR': '#10b981',   # green
            'STRATEGY': '#3b82f6', # blue
            'ANALYSIS': '#f97316', # orange
            'RISK': '#eab308',     # yellow
            'EVENT': '#6366f1',    # indigo
            'OTHER': '#6b7280',    # gray
        }
        
        updated_count = 0
        for category, color in color_map.items():
            tags = Tag.objects.filter(category=category, color='')
            count = tags.update(color=color)
            updated_count += count
        
        self.stdout.write(
            self.style.SUCCESS(f'{updated_count}個のタグの色を更新しました')
        )