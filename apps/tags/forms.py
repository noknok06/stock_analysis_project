# ========================================
# apps/tags/forms.py - タグ管理フォーム
# ========================================

from django import forms
from django.core.exceptions import ValidationError
from apps.tags.models import Tag


class TagForm(forms.ModelForm):
    """タグ作成・編集フォーム"""
    
    class Meta:
        model = Tag
        fields = ['name', 'category', 'description', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '#タグ名を入力',
                'maxlength': 50
            }),
            'category': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'タグの説明を入力（任意）'
            }),
            'color': forms.TextInput(attrs={
                'type': 'hidden'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500'
            })
        }
    
    def clean_name(self):
        """タグ名のバリデーション"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError('タグ名は必須です。')
        
        # #がない場合は自動で追加
        if not name.startswith('#'):
            name = '#' + name
        
        # 長さチェック
        if len(name) > 50:
            raise ValidationError('タグ名は50文字以内で入力してください。')
        
        # 特殊文字チェック
        invalid_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        for char in invalid_chars:
            if char in name:
                raise ValidationError('タグ名に無効な文字が含まれています。')
        
        # 重複チェック（編集時は現在のインスタンスを除外）
        existing_tags = Tag.objects.filter(name=name)
        if self.instance and self.instance.pk:
            existing_tags = existing_tags.exclude(pk=self.instance.pk)
        
        if existing_tags.exists():
            raise ValidationError('このタグ名は既に使用されています。')
        
        return name
    
    def clean_color(self):
        """カラーコードのバリデーション"""
        color = self.cleaned_data.get('color', '').strip()
        
        if not color:
            return '#6b7280'  # デフォルトの灰色
        
        # ヘックスカラーコードの形式チェック
        if not color.startswith('#'):
            color = '#' + color
        
        if len(color) != 7:
            raise ValidationError('有効なカラーコードを入力してください。（例: #ff0000）')
        
        try:
            int(color[1:], 16)
        except ValueError:
            raise ValidationError('有効なカラーコードを入力してください。')
        
        return color


class TagSearchForm(forms.Form):
    """タグ検索フォーム"""
    
    q = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'タグ名または説明で検索...',
            'autocomplete': 'off'
        })
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'すべて')] + Tag.CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'すべて'),
            ('true', 'アクティブ'),
            ('false', '無効')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    usage = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'すべて'),
            ('used', '使用中'),
            ('unused', '未使用')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('-usage_count', '使用回数（多い順）'),
            ('usage_count', '使用回数（少ない順）'),
            ('name', '名前（昇順）'),
            ('-name', '名前（降順）'),
            ('-created_at', '作成日（新しい順）'),
            ('created_at', '作成日（古い順）'),
            ('-updated_at', '更新日（新しい順）'),
            ('updated_at', '更新日（古い順）')
        ],
        initial='-usage_count',
        widget=forms.Select(attrs={
            'class': 'bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )


class TagBulkActionForm(forms.Form):
    """タグ一括操作フォーム"""
    
    ACTION_CHOICES = [
        ('activate', 'アクティブ化'),
        ('deactivate', '無効化'),
        ('delete', '削除'),
        ('change_category', 'カテゴリ変更'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    tag_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    # カテゴリ変更用の追加フィールド
    new_category = forms.ChoiceField(
        required=False,
        choices=Tag.CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    def clean_tag_ids(self):
        """タグIDリストのバリデーション"""
        tag_ids_str = self.cleaned_data.get('tag_ids', '')
        
        if not tag_ids_str:
            raise ValidationError('タグが選択されていません。')
        
        try:
            tag_ids = [int(id_str.strip()) for id_str in tag_ids_str.split(',') if id_str.strip()]
        except ValueError:
            raise ValidationError('無効なタグIDが含まれています。')
        
        if not tag_ids:
            raise ValidationError('タグが選択されていません。')
        
        # 存在確認
        existing_count = Tag.objects.filter(pk__in=tag_ids).count()
        if existing_count != len(tag_ids):
            raise ValidationError('選択されたタグの一部が見つかりません。')
        
        return tag_ids
    
    def clean(self):
        """フォーム全体のバリデーション"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        new_category = cleaned_data.get('new_category')
        
        if action == 'change_category' and not new_category:
            raise ValidationError('カテゴリ変更には新しいカテゴリの選択が必要です。')
        
        return cleaned_data


class TagImportForm(forms.Form):
    """タグインポートフォーム"""
    
    IMPORT_FORMAT_CHOICES = [
        ('csv', 'CSV形式'),
        ('json', 'JSON形式'),
        ('text', 'テキスト形式（1行1タグ）')
    ]
    
    import_file = forms.FileField(
        label='インポートファイル',
        help_text='CSVファイル、JSONファイル、またはテキストファイルを選択してください',
        widget=forms.FileInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'accept': '.csv,.json,.txt'
        })
    )
    
    import_format = forms.ChoiceField(
        choices=IMPORT_FORMAT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    default_category = forms.ChoiceField(
        choices=Tag.CATEGORY_CHOICES,
        initial='OTHER',
        label='デフォルトカテゴリ',
        help_text='カテゴリが指定されていないタグに適用されます',
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    overwrite_existing = forms.BooleanField(
        required=False,
        initial=False,
        label='既存タグを上書き',
        help_text='チェックすると、同名のタグが存在する場合に上書きします',
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500'
        })
    )
    
    def clean_import_file(self):
        """インポートファイルのバリデーション"""
        file = self.cleaned_data.get('import_file')
        
        if not file:
            raise ValidationError('ファイルを選択してください。')
        
        # ファイルサイズチェック（5MB以下）
        if file.size > 5 * 1024 * 1024:
            raise ValidationError('ファイルサイズは5MB以下にしてください。')
        
        # ファイル拡張子チェック
        allowed_extensions = ['.csv', '.json', '.txt']
        file_extension = '.' + file.name.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise ValidationError('対応していないファイル形式です。CSV、JSON、またはテキストファイルを選択してください。')
        
        return file


class TagExportForm(forms.Form):
    """タグエクスポートフォーム"""
    
    EXPORT_FORMAT_CHOICES = [
        ('csv', 'CSV形式'),
        ('json', 'JSON形式'),
        ('xml', 'XML形式')
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMAT_CHOICES,
        initial='csv',
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    include_usage_stats = forms.BooleanField(
        required=False,
        initial=True,
        label='使用統計を含める',
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500'
        })
    )
    
    include_inactive = forms.BooleanField(
        required=False,
        initial=False,
        label='無効なタグも含める',
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500'
        })
    )
    
    selected_categories = forms.MultipleChoiceField(
        required=False,
        choices=Tag.CATEGORY_CHOICES,
        label='エクスポートするカテゴリ',
        help_text='何も選択しない場合は全カテゴリが対象になります',
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'text-blue-600 focus:ring-blue-500'
        })
    )