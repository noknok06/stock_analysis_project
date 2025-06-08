# ========================================
# apps/notes/forms.py - 新しいノート構成対応フォーム
# ========================================

import json
from django import forms
from django.core.exceptions import ValidationError
from apps.notes.models import Notebook, SubNotebook, Entry
from apps.tags.models import Tag
from apps.common.validators import validate_stock_code, validate_json_content

class NotebookTemplateChoiceForm(forms.Form):
    """ノート作成時のテンプレート選択フォーム"""
    
    TEMPLATE_CHOICES = [
        ('theme_multi', 'テーマ型（複数銘柄）'),
        ('watchlist', 'ウォッチリスト'),
        ('portfolio', 'ポートフォリオ管理'),
        ('sector_analysis', 'セクター分析'),
        ('event_tracking', 'イベント追跡'),
        ('research_project', 'リサーチプロジェクト'),
        ('custom', 'カスタム'),
    ]
    
    template_type = forms.ChoiceField(
        choices=TEMPLATE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'template-radio'
        }),
        label='ノートテンプレート'
    )
    
    quick_title = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
            'placeholder': '例: 2025年注目決算、米国グロース株ウォッチ'
        }),
        label='仮タイトル（後で変更可能）'
    )


class NotebookForm(forms.ModelForm):
    """ノートブック作成・編集フォーム（新構造）"""
    
    # JSON配列フィールド
    objectives = forms.CharField(required=False, widget=forms.HiddenInput())
    key_themes = forms.CharField(required=False, widget=forms.HiddenInput())
    selected_tags_json = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = Notebook
        fields = [
            'title', 'subtitle', 'description', 'notebook_type', 
            'status', 'notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 2025年注目決算銘柄',
                'required': True
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 第1四半期業績好調銘柄をウォッチ'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'このノートの目的や方針について説明してください'
            }),
            'notebook_type': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'ノート全体に関するメモやルールを記載'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'ノートタイトル *'
        self.fields['subtitle'].label = 'サブタイトル'
        self.fields['description'].label = '説明'
        self.fields['notebook_type'].label = 'ノートタイプ'
        self.fields['status'].label = 'ステータス'
        self.fields['notes'].label = 'メモ'
    
    def clean_objectives(self):
        """目的・目標のJSONバリデーション"""
        objectives_json = self.cleaned_data.get('objectives', '[]')
        try:
            objectives = json.loads(objectives_json)
            return [obj.strip() for obj in objectives if obj and obj.strip()]
        except (json.JSONDecodeError, TypeError):
            return []
    
    def clean_key_themes(self):
        """キーテーマのJSONバリデーション"""
        themes_json = self.cleaned_data.get('key_themes', '[]')
        try:
            themes = json.loads(themes_json)
            return [theme.strip() for theme in themes if theme and theme.strip()]
        except (json.JSONDecodeError, TypeError):
            return []
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # JSON配列フィールドを保存
        instance.objectives = self.cleaned_data.get('objectives', [])
        instance.key_themes = self.cleaned_data.get('key_themes', [])
        
        if commit:
            instance.save()
            # タグ処理
            self._handle_tags(instance)
        
        return instance
    
    def _handle_tags(self, instance):
        """タグ処理（既存コードを参考に実装）"""
        # 既存のタグ処理ロジックを使用
        pass


class SubNotebookForm(forms.ModelForm):
    """サブノート作成・編集フォーム"""
    
    class Meta:
        model = SubNotebook
        fields = ['title', 'description', 'order_index']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
                'placeholder': '例: 日本株、米国株、決算前注目銘柄'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
                'rows': 2,
                'placeholder': 'このサブノートの説明'
            }),
            'order_index': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2',
                'min': '0'
            }),
        }


class EntryForm(forms.ModelForm):
    """エントリー作成・編集フォーム（新構造）"""
    
    # 動的コンテンツフィールド
    content_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    selected_tags_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = Entry
        fields = [
            'title', 'entry_type', 'stock_code', 'company_name', 'market',
            'event_date', 'event_type', 'summary', 'current_price', 
            'target_price', 'rating', 'importance', 'sub_notebook'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
                'placeholder': '例: トヨタ自動車 2025Q1決算分析',
                'required': True
            }),
            'entry_type': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2'
            }),
            'stock_code': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
                'placeholder': '例: 7203'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
                'placeholder': '例: トヨタ自動車'
            }),
            'market': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
                'placeholder': '例: 東証プライム'
            }),
            'event_date': forms.DateInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2',
                'type': 'date'
            }),
            'event_type': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
                'placeholder': '例: 決算発表、株主総会'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
                'rows': 3,
                'placeholder': 'エントリーの要約を記載（検索用）'
            }),
            'current_price': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
                'step': '0.01'
            }),
            'target_price': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
                'step': '0.01'
            }),
            'rating': forms.Select(choices=[
                ('', '選択してください'),
                ('strong_buy', '強い買い'),
                ('buy', '買い'),
                ('hold', '中立'),
                ('sell', '売り'),
                ('strong_sell', '強い売り'),
            ], attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2'
            }),
            'importance': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2'
            }),
            'sub_notebook': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.notebook = kwargs.pop('notebook', None)
        super().__init__(*args, **kwargs)
        
        # サブノート選択肢を設定
        if self.notebook:
            self.fields['sub_notebook'].queryset = self.notebook.sub_notebooks.all()
            self.fields['sub_notebook'].empty_label = "サブノートを選択（任意）"
    
    def clean_stock_code(self):
        """銘柄コードのバリデーション"""
        stock_code = self.cleaned_data.get('stock_code')
        if stock_code and stock_code.strip():
            try:
                validate_stock_code(stock_code.strip())
                return stock_code.strip()
            except ValidationError as e:
                raise forms.ValidationError(str(e))
        return stock_code
    
    def clean_content_json(self):
        """コンテンツJSONのバリデーション"""
        content_json = self.cleaned_data.get('content_json', '{}')
        try:
            return json.loads(content_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # JSONコンテンツを保存
        instance.content = self.cleaned_data.get('content_json', {})
        
        if commit:
            instance.save()
            # タグ処理
            self._handle_tags(instance)
        
        return instance
    
    def _handle_tags(self, instance):
        """タグ処理"""
        # 既存のタグ処理ロジックを使用
        pass


class QuickEntryForm(forms.Form):
    """クイックエントリー作成フォーム"""
    
    QUICK_ENTRY_TYPES = [
        ('stock_memo', '銘柄メモ'),
        ('price_alert', '価格変動'),
        ('news_clip', 'ニュースメモ'),
        ('quick_analysis', '簡易分析'),
    ]
    
    entry_type = forms.ChoiceField(
        choices=QUICK_ENTRY_TYPES,
        widget=forms.RadioSelect(),
        label='エントリータイプ'
    )
    
    stock_code = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2',
            'placeholder': '銘柄コード（任意）'
        })
    )
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2',
            'placeholder': 'タイトル'
        })
    )
    
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2',
            'rows': 4,
            'placeholder': '内容を入力してください'
        })
    )


class SearchForm(forms.Form):
    """拡張検索フォーム（新構造対応）"""
    
    q = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2',
            'placeholder': '銘柄名、内容、タグで検索...'
        }),
        label='検索語'
    )
    
    notebook_type = forms.ChoiceField(
        choices=[('', 'すべて')] + Notebook.NOTEBOOK_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2'
        }),
        label='ノートタイプ'
    )
    
    entry_type = forms.ChoiceField(
        choices=[('', 'すべて')] + Entry.ENTRY_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2'
        }),
        label='エントリータイプ'
    )
    
    stock_code = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2',
            'placeholder': '銘柄コード'
        }),
        label='銘柄コード'
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2',
            'type': 'date'
        }),
        label='開始日'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2',
            'type': 'date'
        }),
        label='終了日'
    )
    
    bookmarked_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'text-blue-600 bg-gray-700 border-gray-600 rounded'
        }),
        label='ブックマークのみ'
    )