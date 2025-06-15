# ========================================
# apps/tags/management/commands/manage_tags.py - ユーザー固有タグ管理コマンド
# ========================================

import json
import csv
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q
from apps.tags.models import Tag
from apps.notes.models import Notebook, Entry


class Command(BaseCommand):
    """ユーザー固有タグ管理コマンド"""
    help = 'ユーザー固有タグの管理処理を実行します'
    
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='実行するアクション')
        
        # ユーザー指定の共通オプション
        def add_user_argument(subparser):
            subparser.add_argument(
                '--user',
                type=str,
                help='対象ユーザー名（指定しない場合は全ユーザー）'
            )
        
        # クリーンアップコマンド
        cleanup_parser = subparsers.add_parser('cleanup', help='未使用タグの整理')
        add_user_argument(cleanup_parser)
        cleanup_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際に削除せずに対象を表示'
        )
        cleanup_parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='指定日数以上使用されていないタグが対象（デフォルト: 30日）'
        )
        cleanup_parser.add_argument(
            '--force',
            action='store_true',
            help='確認なしで実行'
        )
        
        # 統計表示コマンド
        stats_parser = subparsers.add_parser('stats', help='タグ統計の表示')
        add_user_argument(stats_parser)
        stats_parser.add_argument(
            '--detailed',
            action='store_true',
            help='詳細統計を表示'
        )
        stats_parser.add_argument(
            '--category',
            choices=[choice[0] for choice in Tag.CATEGORY_CHOICES],
            help='特定カテゴリの統計のみ表示'
        )
        
        # 使用回数更新コマンド
        update_parser = subparsers.add_parser('update-counts', help='使用回数の再計算')
        add_user_argument(update_parser)
        update_parser.add_argument(
            '--all',
            action='store_true',
            help='すべてのタグの使用回数を再計算'
        )
        
        # 重複チェックコマンド
        duplicate_parser = subparsers.add_parser('check-duplicates', help='重複タグのチェック')
        add_user_argument(duplicate_parser)
        duplicate_parser.add_argument(
            '--merge',
            action='store_true',
            help='重複タグを自動マージ'
        )
        
        # エクスポートコマンド
        export_parser = subparsers.add_parser('export', help='タグのエクスポート')
        add_user_argument(export_parser)
        export_parser.add_argument(
            '--format',
            choices=['csv', 'json', 'xml'],
            default='csv',
            help='エクスポート形式'
        )
        export_parser.add_argument(
            '--output',
            help='出力ファイル名'
        )
        export_parser.add_argument(
            '--include-inactive',
            action='store_true',
            help='無効なタグも含める'
        )
        
        # インポートコマンド
        import_parser = subparsers.add_parser('import', help='タグのインポート')
        import_parser.add_argument(
            '--user',
            type=str,
            required=True,
            help='インポート先ユーザー名'
        )
        import_parser.add_argument(
            'file',
            help='インポートするファイル'
        )
        import_parser.add_argument(
            '--format',
            choices=['csv', 'json'],
            default='csv',
            help='インポート形式'
        )
        import_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際にインポートせずに内容を確認'
        )
        
        # バックアップコマンド
        backup_parser = subparsers.add_parser('backup', help='タグデータのバックアップ')
        add_user_argument(backup_parser)
        backup_parser.add_argument(
            '--output-dir',
            default='./backups',
            help='バックアップ保存ディレクトリ'
        )
    
    def handle(self, *args, **options):
        action = options.get('action')
        
        if not action:
            self.print_help()
            return
        
        try:
            if action == 'cleanup':
                self.cleanup_tags(options)
            elif action == 'stats':
                self.show_stats(options)
            elif action == 'update-counts':
                self.update_usage_counts(options)
            elif action == 'check-duplicates':
                self.check_duplicates(options)
            elif action == 'export':
                self.export_tags(options)
            elif action == 'import':
                self.import_tags(options)
            elif action == 'backup':
                self.backup_tags(options)
            else:
                raise CommandError(f'Unknown action: {action}')
                
        except Exception as e:
            raise CommandError(f'Error executing {action}: {str(e)}')
    
    def get_users(self, username=None):
        """対象ユーザーを取得"""
        if username:
            try:
                return [User.objects.get(username=username)]
            except User.DoesNotExist:
                raise CommandError(f'User "{username}" not found')
        else:
            return User.objects.filter(tag__isnull=False).distinct()
    
    def cleanup_tags(self, options):
        """未使用タグのクリーンアップ"""
        days = options['days']
        dry_run = options['dry_run']
        force = options['force']
        username = options.get('user')
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        users = self.get_users(username)
        total_deleted = 0
        
        for user in users:
            self.stdout.write(f'\n=== ユーザー: {user.username} ===')
            
            # 未使用タグを特定
            unused_tags = Tag.objects.filter(
                user=user,
                Q(usage_count=0) | Q(updated_at__lt=cutoff_date),
                is_active=True
            ).annotate(
                notebook_count=Count('notebook'),
                entry_count=Count('entry')
            ).filter(
                notebook_count=0,
                entry_count=0
            )
            
            self.stdout.write(f'対象期間: {days}日以上未使用')
            self.stdout.write(f'対象タグ数: {unused_tags.count()}件')
            
            if unused_tags.count() == 0:
                self.stdout.write(self.style.SUCCESS('クリーンアップ対象のタグはありません'))
                continue
            
            # 対象タグの詳細表示
            for tag in unused_tags[:5]:  # 最初の5件を表示
                self.stdout.write(f'  - {tag.name} ({tag.get_category_display()}) - 最終更新: {tag.updated_at.strftime("%Y-%m-%d")}')
            
            if unused_tags.count() > 5:
                self.stdout.write(f'  ... 他 {unused_tags.count() - 5}件')
            
            if dry_run:
                self.stdout.write(self.style.WARNING('[DRY RUN] 実際の削除は行いません'))
                continue
            
            # 確認
            if not force:
                confirm = input(f'{user.username}の{unused_tags.count()}件のタグを無効化しますか？ [y/N]: ')
                if confirm.lower() != 'y':
                    self.stdout.write('スキップしました')
                    continue
            
            # 無効化実行
            updated_count = unused_tags.update(is_active=False)
            total_deleted += updated_count
            self.stdout.write(self.style.SUCCESS(f'{updated_count}件のタグを無効化しました'))
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n合計: {total_deleted}件のタグを無効化しました'))
    
    def show_stats(self, options):
        """タグ統計の表示"""
        detailed = options['detailed']
        category = options.get('category')
        username = options.get('user')
        
        users = self.get_users(username)
        
        self.stdout.write('\n=== ユーザー別タグ統計 ===\n')
        
        for user in users:
            self.stdout.write(f'--- {user.username} ---')
            
            user_tags = Tag.objects.filter(user=user)
            
            # 基本統計
            total_tags = user_tags.count()
            active_tags = user_tags.filter(is_active=True).count()
            used_tags = user_tags.filter(usage_count__gt=0).count()
            total_usage = sum(user_tags.values_list('usage_count', flat=True))
            
            self.stdout.write(f'総タグ数: {total_tags}')
            self.stdout.write(f'アクティブタグ数: {active_tags}')
            self.stdout.write(f'使用中タグ数: {used_tags}')
            self.stdout.write(f'総使用回数: {total_usage}')
            
            # カテゴリ別統計
            self.stdout.write('\n--- カテゴリ別統計 ---')
            categories = Tag.CATEGORY_CHOICES
            if category:
                categories = [(category, dict(Tag.CATEGORY_CHOICES)[category])]
            
            for cat_code, cat_name in categories:
                cat_tags = user_tags.filter(category=cat_code)
                cat_count = cat_tags.count()
                cat_active = cat_tags.filter(is_active=True).count()
                cat_usage = sum(cat_tags.values_list('usage_count', flat=True))
                
                if cat_count > 0:
                    self.stdout.write(f'{cat_name}: {cat_count}件 (アクティブ: {cat_active}件, 使用回数: {cat_usage}回)')
            
            if detailed:
                self.stdout.write('\n--- 詳細統計 ---')
                
                # 最も使用されているタグ TOP 5
                top_tags = user_tags.filter(usage_count__gt=0).order_by('-usage_count')[:5]
                if top_tags:
                    self.stdout.write('\n最も使用されているタグ TOP 5:')
                    for i, tag in enumerate(top_tags, 1):
                        self.stdout.write(f'  {i:2d}. {tag.name} - {tag.usage_count}回')
                
                # 最近作成されたタグ
                recent_tags = user_tags.order_by('-created_at')[:3]
                if recent_tags:
                    self.stdout.write('\n最近作成されたタグ:')
                    for tag in recent_tags:
                        self.stdout.write(f'  - {tag.name} - {tag.created_at.strftime("%Y-%m-%d %H:%M")}')
                
                # 未使用タグ
                unused_tags = user_tags.filter(usage_count=0)
                self.stdout.write(f'\n未使用タグ数: {unused_tags.count()}件')
            
            self.stdout.write('')  # 空行
    
    def update_usage_counts(self, options):
        """使用回数の再計算"""
        update_all = options['all']
        username = options.get('user')
        
        users = self.get_users(username)
        
        self.stdout.write('\n=== 使用回数更新 ===\n')
        
        total_updated = 0
        
        for user in users:
            self.stdout.write(f'--- {user.username} ---')
            
            user_tags = Tag.objects.filter(user=user)
            if not update_all:
                user_tags = user_tags.filter(usage_count=0)
            
            tag_count = user_tags.count()
            self.stdout.write(f'対象タグ数: {tag_count}件')
            
            updated_count = 0
            for i, tag in enumerate(user_tags, 1):
                # ノートブックとエントリーでの使用回数を計算
                notebook_count = Notebook.objects.filter(user=user, tags=tag).count()
                entry_count = Entry.objects.filter(notebook__user=user, tags=tag).count()
                new_count = notebook_count + entry_count
                
                if tag.usage_count != new_count:
                    tag.usage_count = new_count
                    tag.save(update_fields=['usage_count'])
                    updated_count += 1
                
                if i % 50 == 0:
                    self.stdout.write(f'処理中... {i}/{tag_count}')
            
            self.stdout.write(self.style.SUCCESS(f'完了: {updated_count}件のタグの使用回数を更新しました'))
            total_updated += updated_count
        
        self.stdout.write(self.style.SUCCESS(f'\n合計: {total_updated}件のタグの使用回数を更新しました'))
    
    def check_duplicates(self, options):
        """重複タグのチェック"""
        merge = options['merge']
        username = options.get('user')
        
        users = self.get_users(username)
        
        self.stdout.write('\n=== 重複タグチェック ===\n')
        
        total_merged = 0
        
        for user in users:
            self.stdout.write(f'--- {user.username} ---')
            
            # ユーザー内での類似名のタグを検索
            duplicates = []
            processed_names = set()
            
            for tag in Tag.objects.filter(user=user):
                if tag.name.lower() in processed_names:
                    continue
                
                similar_tags = Tag.objects.filter(
                    user=user,
                    name__iexact=tag.name
                ).exclude(pk=tag.pk)
                
                if similar_tags.exists():
                    duplicates.append({
                        'primary': tag,
                        'duplicates': list(similar_tags)
                    })
                
                processed_names.add(tag.name.lower())
            
            if not duplicates:
                self.stdout.write(self.style.SUCCESS('重複タグは見つかりませんでした'))
                continue
            
            self.stdout.write(f'重複グループ数: {len(duplicates)}')
            
            for group in duplicates:
                primary = group['primary']
                dupes = group['duplicates']
                
                self.stdout.write(f'\nグループ: {primary.name}')
                self.stdout.write(f'  メイン: {primary.name} (使用回数: {primary.usage_count})')
                
                for dupe in dupes:
                    self.stdout.write(f'  重複: {dupe.name} (使用回数: {dupe.usage_count})')
                
                if merge:
                    # 使用回数の多いタグをメインとして統合
                    all_tags = [primary] + dupes
                    main_tag = max(all_tags, key=lambda t: t.usage_count)
                    
                    total_usage = sum(t.usage_count for t in all_tags)
                    
                    # 重複タグを削除
                    for tag in all_tags:
                        if tag != main_tag:
                            tag.delete()
                            total_merged += 1
                    
                    # メインタグの使用回数を更新
                    main_tag.usage_count = total_usage
                    main_tag.save()
                    
                    self.stdout.write(f'  → {main_tag.name} に統合しました')
        
        if merge and total_merged > 0:
            self.stdout.write(self.style.SUCCESS(f'\n合計: {total_merged}件の重複タグを統合しました'))
    
    def export_tags(self, options):
        """タグのエクスポート"""
        format_type = options['format']
        output_file = options.get('output')
        include_inactive = options['include_inactive']
        username = options.get('user')
        
        users = self.get_users(username)
        
        # ファイル名の生成
        if not output_file:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            user_suffix = f'_{username}' if username else '_all_users'
            output_file = f'tags_export{user_suffix}_{timestamp}.{format_type}'
        
        # タグデータの取得
        all_tags = []
        for user in users:
            user_tags = Tag.objects.filter(user=user)
            if not include_inactive:
                user_tags = user_tags.filter(is_active=True)
            all_tags.extend(user_tags)
        
        # エクスポート実行
        if format_type == 'csv':
            self._export_csv(all_tags, output_file)
        elif format_type == 'json':
            self._export_json(all_tags, output_file)
        elif format_type == 'xml':
            self._export_xml(all_tags, output_file)
        
        self.stdout.write(self.style.SUCCESS(f'エクスポート完了: {output_file} ({len(all_tags)}件)'))
    
    def _export_csv(self, tags, filename):
        """CSV形式でエクスポート"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['user', 'name', 'category', 'description', 'usage_count', 'is_active', 'created_at', 'updated_at'])
            
            for tag in tags:
                writer.writerow([
                    tag.user.username,
                    tag.name,
                    tag.category,
                    tag.description,
                    tag.usage_count,
                    tag.is_active,
                    tag.created_at.isoformat(),
                    tag.updated_at.isoformat()
                ])
    
    def _export_json(self, tags, filename):
        """JSON形式でエクスポート"""
        data = []
        for tag in tags:
            data.append({
                'user': tag.user.username,
                'name': tag.name,
                'category': tag.category,
                'description': tag.description,
                'usage_count': tag.usage_count,
                'is_active': tag.is_active,
                'created_at': tag.created_at.isoformat(),
                'updated_at': tag.updated_at.isoformat()
            })
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
    
    def _export_xml(self, tags, filename):
        """XML形式でエクスポート"""
        with open(filename, 'w', encoding='utf-8') as xmlfile:
            xmlfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            xmlfile.write('<tags>\n')
            
            for tag in tags:
                xmlfile.write('  <tag>\n')
                xmlfile.write(f'    <user>{self._escape_xml(tag.user.username)}</user>\n')
                xmlfile.write(f'    <name>{self._escape_xml(tag.name)}</name>\n')
                xmlfile.write(f'    <category>{tag.category}</category>\n')
                xmlfile.write(f'    <description>{self._escape_xml(tag.description)}</description>\n')
                xmlfile.write(f'    <usage_count>{tag.usage_count}</usage_count>\n')
                xmlfile.write(f'    <is_active>{tag.is_active}</is_active>\n')
                xmlfile.write(f'    <created_at>{tag.created_at.isoformat()}</created_at>\n')
                xmlfile.write(f'    <updated_at>{tag.updated_at.isoformat()}</updated_at>\n')
                xmlfile.write('  </tag>\n')
            
            xmlfile.write('</tags>\n')
    
    def import_tags(self, options):
        """タグのインポート"""
        filename = options['file']
        format_type = options['format']
        dry_run = options['dry_run']
        username = options['user']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" not found')
        
        self.stdout.write(f'\n=== タグインポート ===')
        self.stdout.write(f'ファイル: {filename}')
        self.stdout.write(f'形式: {format_type}')
        self.stdout.write(f'対象ユーザー: {username}')
        
        try:
            if format_type == 'csv':
                tags_data = self._import_csv(filename)
            elif format_type == 'json':
                tags_data = self._import_json(filename)
            else:
                raise CommandError(f'Unsupported format: {format_type}')
            
            self.stdout.write(f'読み込んだタグ数: {len(tags_data)}件')
            
            if dry_run:
                self.stdout.write('\n[DRY RUN] インポート対象:')
                for i, tag_data in enumerate(tags_data[:10], 1):
                    self.stdout.write(f'  {i}. {tag_data["name"]} ({tag_data["category"]})')
                if len(tags_data) > 10:
                    self.stdout.write(f'  ... 他 {len(tags_data) - 10}件')
                return
            
            # インポート実行
            created_count = 0
            updated_count = 0
            
            for tag_data in tags_data:
                tag, created = Tag.objects.get_or_create(
                    user=user,
                    name=tag_data['name'],
                    defaults={
                        'category': tag_data.get('category', 'OTHER'),
                        'description': tag_data.get('description', ''),
                        'usage_count': tag_data.get('usage_count', 0),
                        'is_active': tag_data.get('is_active', True)
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    # 既存タグの更新
                    tag.category = tag_data.get('category', tag.category)
                    tag.description = tag_data.get('description', tag.description)
                    tag.is_active = tag_data.get('is_active', tag.is_active)
                    tag.save()
                    updated_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'インポート完了: 新規 {created_count}件, 更新 {updated_count}件'))
            
        except FileNotFoundError:
            raise CommandError(f'ファイルが見つかりません: {filename}')
        except Exception as e:
            raise CommandError(f'インポートエラー: {str(e)}')
    
    def _import_csv(self, filename):
        """CSVファイルからタグデータを読み込み"""
        tags_data = []
        
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                tags_data.append({
                    'name': row.get('name', '').strip(),
                    'category': row.get('category', 'OTHER').upper(),
                    'description': row.get('description', ''),
                    'usage_count': int(row.get('usage_count', 0)),
                    'is_active': row.get('is_active', 'true').lower() == 'true'
                })
        
        return tags_data
    
    def _import_json(self, filename):
        """JSONファイルからタグデータを読み込み"""
        with open(filename, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        
        if isinstance(data, list):
            return data
        else:
            raise ValueError('JSON file must contain an array of tag objects')
    
    def backup_tags(self, options):
        """タグデータのバックアップ"""
        import os
        from pathlib import Path
        
        output_dir = Path(options['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        username = options.get('user')
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        users = self.get_users(username)
        
        for user in users:
            # ユーザー別にバックアップファイルを作成
            backup_file = output_dir / f'tags_backup_{user.username}_{timestamp}.json'
            
            user_tags = Tag.objects.filter(user=user)
            backup_data = {
                'user': user.username,
                'timestamp': timezone.now().isoformat(),
                'total_count': user_tags.count(),
                'tags': []
            }
            
            for tag in user_tags:
                backup_data['tags'].append({
                    'name': tag.name,
                    'category': tag.category,
                    'description': tag.description,
                    'usage_count': tag.usage_count,
                    'is_active': tag.is_active,
                    'created_at': tag.created_at.isoformat(),
                    'updated_at': tag.updated_at.isoformat()
                })
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.stdout.write(self.style.SUCCESS(f'バックアップ完了: {backup_file} ({user_tags.count()}件)'))
    
    def _escape_xml(self, text):
        """XML用エスケープ"""
        if not text:
            return ''
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))
    
    def print_help(self):
        """ヘルプメッセージの表示"""
        self.stdout.write('''
ユーザー固有タグ管理コマンド

使用方法:
  python manage.py manage_tags <action> [options]

利用可能なアクション:
  cleanup           - 未使用タグの整理
  stats             - タグ統計の表示
  update-counts     - 使用回数の再計算
  check-duplicates  - 重複タグのチェック
  export            - タグのエクスポート
  import            - タグのインポート
  backup            - タグデータのバックアップ

ユーザー指定オプション:
  --user USERNAME   - 特定ユーザーのタグのみ処理

詳細なオプションについては各アクションに --help を付けて実行してください。

例:
  python manage.py manage_tags cleanup --user demo_user --dry-run
  python manage.py manage_tags stats --user demo_user --detailed
  python manage.py manage_tags export --user demo_user --format json --output user_tags.json
  python manage.py manage_tags import --user demo_user tags.csv --format csv
        ''')