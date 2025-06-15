# ========================================
# apps/tags/management/commands/manage_tags.py - タグ管理コマンド
# ========================================

import json
import csv
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Count, Q
from apps.tags.models import Tag
from apps.notes.models import Notebook, Entry


class Command(BaseCommand):
    """タグ管理コマンド"""
    help = 'タグの管理処理を実行します'
    
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='実行するアクション')
        
        # クリーンアップコマンド
        cleanup_parser = subparsers.add_parser('cleanup', help='未使用タグの整理')
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
        update_parser.add_argument(
            '--all',
            action='store_true',
            help='すべてのタグの使用回数を再計算'
        )
        
        # 重複チェックコマンド
        duplicate_parser = subparsers.add_parser('check-duplicates', help='重複タグのチェック')
        duplicate_parser.add_argument(
            '--merge',
            action='store_true',
            help='重複タグを自動マージ'
        )
        
        # エクスポートコマンド
        export_parser = subparsers.add_parser('export', help='タグのエクスポート')
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
    
    def cleanup_tags(self, options):
        """未使用タグのクリーンアップ"""
        days = options['days']
        dry_run = options['dry_run']
        force = options['force']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # 未使用タグを特定
        unused_tags = Tag.objects.filter(
            Q(usage_count=0) | Q(updated_at__lt=cutoff_date),
            is_active=True
        ).annotate(
            notebook_count=Count('notebook'),
            entry_count=Count('entry')
        ).filter(
            notebook_count=0,
            entry_count=0
        )
        
        self.stdout.write(f'\n=== タグクリーンアップ ===')
        self.stdout.write(f'対象期間: {days}日以上未使用')
        self.stdout.write(f'対象タグ数: {unused_tags.count()}件\n')
        
        if unused_tags.count() == 0:
            self.stdout.write(self.style.SUCCESS('クリーンアップ対象のタグはありません'))
            return
        
        # 対象タグの詳細表示
        for tag in unused_tags[:10]:  # 最初の10件を表示
            self.stdout.write(f'  - {tag.name} ({tag.get_category_display()}) - 最終更新: {tag.updated_at.strftime("%Y-%m-%d")}')
        
        if unused_tags.count() > 10:
            self.stdout.write(f'  ... 他 {unused_tags.count() - 10}件')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] 実際の削除は行いません'))
            return
        
        # 確認
        if not force:
            confirm = input(f'\n{unused_tags.count()}件のタグを無効化しますか？ [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('キャンセルしました')
                return
        
        # 無効化実行
        updated_count = unused_tags.update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f'{updated_count}件のタグを無効化しました'))
    
    def show_stats(self, options):
        """タグ統計の表示"""
        detailed = options['detailed']
        category = options.get('category')
        
        self.stdout.write('\n=== タグ統計 ===\n')
        
        # 基本統計
        total_tags = Tag.objects.count()
        active_tags = Tag.objects.filter(is_active=True).count()
        used_tags = Tag.objects.filter(usage_count__gt=0).count()
        total_usage = sum(Tag.objects.values_list('usage_count', flat=True))
        
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
            cat_tags = Tag.objects.filter(category=cat_code)
            cat_count = cat_tags.count()
            cat_active = cat_tags.filter(is_active=True).count()
            cat_usage = sum(cat_tags.values_list('usage_count', flat=True))
            
            self.stdout.write(f'{cat_name}: {cat_count}件 (アクティブ: {cat_active}件, 使用回数: {cat_usage}回)')
        
        if detailed:
            self.stdout.write('\n--- 詳細統計 ---')
            
            # 最も使用されているタグ TOP 10
            top_tags = Tag.objects.filter(usage_count__gt=0).order_by('-usage_count')[:10]
            self.stdout.write('\n最も使用されているタグ TOP 10:')
            for i, tag in enumerate(top_tags, 1):
                self.stdout.write(f'  {i:2d}. {tag.name} - {tag.usage_count}回')
            
            # 最近作成されたタグ
            recent_tags = Tag.objects.order_by('-created_at')[:5]
            self.stdout.write('\n最近作成されたタグ:')
            for tag in recent_tags:
                self.stdout.write(f'  - {tag.name} - {tag.created_at.strftime("%Y-%m-%d %H:%M")}')
            
            # 未使用タグ
            unused_tags = Tag.objects.filter(usage_count=0)
            self.stdout.write(f'\n未使用タグ数: {unused_tags.count()}件')
    
    def update_usage_counts(self, options):
        """使用回数の再計算"""
        update_all = options['all']
        
        self.stdout.write('\n=== 使用回数更新 ===\n')
        
        tags = Tag.objects.all() if update_all else Tag.objects.filter(usage_count=0)
        total_tags = tags.count()
        
        self.stdout.write(f'対象タグ数: {total_tags}件')
        
        updated_count = 0
        for i, tag in enumerate(tags, 1):
            # ノートブックとエントリーでの使用回数を計算
            notebook_count = Notebook.objects.filter(tags=tag).count()
            entry_count = Entry.objects.filter(tags=tag).count()
            new_count = notebook_count + entry_count
            
            if tag.usage_count != new_count:
                tag.usage_count = new_count
                tag.save(update_fields=['usage_count'])
                updated_count += 1
            
            if i % 100 == 0:
                self.stdout.write(f'処理中... {i}/{total_tags}')
        
        self.stdout.write(self.style.SUCCESS(f'完了: {updated_count}件のタグの使用回数を更新しました'))
    
    def check_duplicates(self, options):
        """重複タグのチェック"""
        merge = options['merge']
        
        self.stdout.write('\n=== 重複タグチェック ===\n')
        
        # 類似名のタグを検索
        duplicates = []
        processed_names = set()
        
        for tag in Tag.objects.all():
            if tag.name.lower() in processed_names:
                continue
            
            similar_tags = Tag.objects.filter(
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
            return
        
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
                
                # メインタグの使用回数を更新
                main_tag.usage_count = total_usage
                main_tag.save()
                
                self.stdout.write(f'  → {main_tag.name} に統合しました')
    
    def export_tags(self, options):
        """タグのエクスポート"""
        format_type = options['format']
        output_file = options.get('output')
        include_inactive = options['include_inactive']
        
        # ファイル名の生成
        if not output_file:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'tags_export_{timestamp}.{format_type}'
        
        # タグデータの取得
        tags = Tag.objects.all()
        if not include_inactive:
            tags = tags.filter(is_active=True)
        
        # エクスポート実行
        if format_type == 'csv':
            self._export_csv(tags, output_file)
        elif format_type == 'json':
            self._export_json(tags, output_file)
        elif format_type == 'xml':
            self._export_xml(tags, output_file)
        
        self.stdout.write(self.style.SUCCESS(f'エクスポート完了: {output_file} ({tags.count()}件)'))
    
    def _export_csv(self, tags, filename):
        """CSV形式でエクスポート"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['name', 'category', 'description', 'usage_count', 'is_active', 'created_at', 'updated_at'])
            
            for tag in tags:
                writer.writerow([
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
        
        self.stdout.write(f'\n=== タグインポート ===')
        self.stdout.write(f'ファイル: {filename}')
        self.stdout.write(f'形式: {format_type}')
        
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
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON形式でバックアップ
        backup_file = output_dir / f'tags_backup_{timestamp}.json'
        
        tags = Tag.objects.all()
        backup_data = {
            'timestamp': timezone.now().isoformat(),
            'total_count': tags.count(),
            'tags': []
        }
        
        for tag in tags:
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
        
        self.stdout.write(self.style.SUCCESS(f'バックアップ完了: {backup_file} ({tags.count()}件)'))
    
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
タグ管理コマンド

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

詳細なオプションについては各アクションに --help を付けて実行してください。

例:
  python manage.py manage_tags cleanup --dry-run
  python manage.py manage_tags stats --detailed
  python manage.py manage_tags export --format json --output tags.json
        ''')