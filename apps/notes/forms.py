# ========================================
# apps/notes/forms.py - 見直し版（テーマ単位ノート対応）
# ========================================

import json
from django import forms
from django.core.exceptions import ValidationError
from apps.notes.models import Notebook, Entry, SubNotebook, NotebookTemplate
from apps.tags.models import Tag
from apps.common.validators import validate_stock_code, validate_json_content

class NotebookForm(forms.ModelForm):
    """ノートブック作成・編集フォーム（テーマ単位）"""
    
    # テンプレート選択
    template = forms.ModelChoiceField(
        queryset=NotebookTemplate.objects.filter(is_active=True),
        required=False,
        empty_label="テンプレートを選択（任意）",
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    # JSON配列フィールド
    key_criteria = forms.CharField(required=False, widget=forms.HiddenInput())
    risk_factors = forms.CharField(required=False, widget=forms.HiddenInput())
    selected_tags_json = forms.CharField(required=False, widget=forms.HiddenInput())
    sub_notebooks_json = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = Notebook
        fields = [
            'title', 'subtitle', 'description', 'notebook_type',
            'investment_strategy', 'target_allocation', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 2025年 高配当株ウォッチ',
                'required': True
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 配当利回り3%以上の安定銘柄を選定'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'このノートの目的や投資方針を記述してください'
            }),
            'notebook_type': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'investment_strategy': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'このテーマの投資戦略や方針を記述してください',
                'required': True
            }),
            'target_allocation': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: ポートフォリオの30%、月額3万円'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """フォーム初期化"""
        super().__init__(*args, **kwargs)
        
        # 必須フィールドのラベルに * を追加
        self.fields['title'].label = 'ノートタイトル *'
        self.fields['investment_strategy'].label = '投資戦略 *'
        
        # ヘルプテキストの追加
        self.fields['notebook_type'].help_text = 'ノートの種類を選択してください'
        self.fields['investment_strategy'].help_text = 'このテーマでの投資方針や戦略を明確に記述してください'
    
    def clean_title(self):
        """タイトルのバリデーション"""
        title = self.cleaned_data.get('title')
        if not title or not title.strip():
            raise forms.ValidationError('ノートタイトルは必須です。')
        
        # 既存ノートとの重複チェック（編集時は除外）
        title = title.strip()
        existing_notebooks = Notebook.objects.filter(title=title)
        
        # 編集時は自分自身を除外
        if self.instance and self.instance.pk:
            existing_notebooks = existing_notebooks.exclude(pk=self.instance.pk)
        
        if existing_notebooks.exists():
            raise forms.ValidationError('同じタイトルのノートが既に存在します。')
        
        return title
    
    def clean_investment_strategy(self):
        """投資戦略のバリデーション"""
        investment_strategy = self.cleaned_data.get('investment_strategy')
        if not investment_strategy or not investment_strategy.strip():
            raise forms.ValidationError('投資戦略は必須です。')
        
        # 最小文字数チェック
        if len(investment_strategy.strip()) < 10:
            raise forms.ValidationError('投資戦略は10文字以上で入力してください。')
        
        return investment_strategy.strip()
    
    def clean_key_criteria(self):
        """選定基準のJSONバリデーション"""
        key_criteria_json = self.cleaned_data.get('key_criteria', '[]')
        try:
            key_criteria = json.loads(key_criteria_json)
            if not isinstance(key_criteria, list):
                raise ValidationError('選定基準は配列形式である必要があります')
            
            # 空文字列・None・空白のみの要素を除去
            cleaned_criteria = []
            for criteria in key_criteria:
                if criteria and isinstance(criteria, str) and criteria.strip():
                    cleaned_criteria.append(criteria.strip())
            
            # 重複除去
            cleaned_criteria = list(dict.fromkeys(cleaned_criteria))
            
            return cleaned_criteria
        except (json.JSONDecodeError, TypeError):
            return []
    
    def clean_risk_factors(self):
        """リスク要因のJSONバリデーション"""
        risk_factors_json = self.cleaned_data.get('risk_factors', '[]')
        try:
            risk_factors = json.loads(risk_factors_json)
            if not isinstance(risk_factors, list):
                raise ValidationError('リスク要因は配列形式である必要があります')
            
            # 空文字列・None・空白のみの要素を除去
            cleaned_factors = []
            for factor in risk_factors:
                if factor and isinstance(factor, str) and factor.strip():
                    cleaned_factors.append(factor.strip())
            
            # 重複除去
            cleaned_factors = list(dict.fromkeys(cleaned_factors))
            
            return cleaned_factors
        except (json.JSONDecodeError, TypeError):
            return []
    
    def clean_selected_tags_json(self):
        """タグJSONのバリデーション"""
        tags_json = self.cleaned_data.get('selected_tags_json', '{}')
        try:
            tags_data = json.loads(tags_json)
            if not isinstance(tags_data, dict):
                raise ValidationError('タグデータは辞書形式である必要があります')
            
            # デフォルト構造を確保
            if 'selected' not in tags_data:
                tags_data['selected'] = []
            if 'changes' not in tags_data:
                tags_data['changes'] = {'added': [], 'removed': []}
            
            # 選択されたタグの重複除去と検証
            selected_tags = []
            for tag_name in tags_data.get('selected', []):
                if tag_name and isinstance(tag_name, str) and tag_name.strip():
                    tag_name = tag_name.strip()
                    # #がない場合は自動で追加
                    if not tag_name.startswith('#'):
                        tag_name = '#' + tag_name
                    if tag_name not in selected_tags:
                        selected_tags.append(tag_name)
            
            tags_data['selected'] = selected_tags
            
            return tags_data
        except (json.JSONDecodeError, TypeError):
            return {'selected': [], 'changes': {'added': [], 'removed': []}}
    
    def clean_sub_notebooks_json(self):
        """サブノートJSONのバリデーション"""
        sub_notebooks_json = self.cleaned_data.get('sub_notebooks_json', '[]')
        try:
            sub_notebooks = json.loads(sub_notebooks_json)
            if not isinstance(sub_notebooks, list):
                raise ValidationError('サブノートは配列形式である必要があります')
            
            # 有効なサブノート名のみ抽出
            cleaned_sub_notebooks = []
            for sub_notebook in sub_notebooks:
                if isinstance(sub_notebook, str) and sub_notebook.strip():
                    cleaned_sub_notebooks.append(sub_notebook.strip())
                elif isinstance(sub_notebook, dict) and 'title' in sub_notebook:
                    title = sub_notebook['title'].strip()
                    if title:
                        cleaned_sub_notebooks.append({
                            'title': title,
                            'description': sub_notebook.get('description', '').strip()
                        })
            
            return cleaned_sub_notebooks
        except (json.JSONDecodeError, TypeError):
            return []
    
    def save(self, commit=True):
        """保存処理でタグとサブノートを処理"""
        instance = super().save(commit=False)
        
        # JSON配列フィールドを保存
        instance.key_criteria = self.cleaned_data.get('key_criteria', [])
        instance.risk_factors = self.cleaned_data.get('risk_factors', [])
        
        if commit:
            instance.save()
            
            # タグの処理
            self._handle_tags(instance)
            
            # サブノートの処理
            self._handle_sub_notebooks(instance)
        
        return instance
    
    def _handle_tags(self, instance):
        """タグの追加・削除処理"""
        try:
            tags_data = self.cleaned_data.get('selected_tags_json', {})
            selected_tags = tags_data.get('selected', [])
            changes = tags_data.get('changes', {})
            
            # 編集時：既存タグの削除処理
            if self.instance.pk:
                removed_tag_ids = changes.get('removed', [])
                for tag_id in removed_tag_ids:
                    try:
                        tag = Tag.objects.get(pk=tag_id)
                        instance.tags.remove(tag)
                    except (Tag.DoesNotExist, ValueError):
                        continue
            else:
                # 新規作成時：既存タグをクリア
                instance.tags.clear()
            
            # 選択されたタグを処理・追加
            for tag_name in selected_tags:
                if not tag_name.strip():
                    continue
                    
                # #がない場合は自動で追加
                if not tag_name.startswith('#'):
                    tag_name = '#' + tag_name
                
                # タグを取得または作成
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={
                        'category': self._determine_tag_category(tag_name),
                        'description': self._generate_tag_description(tag_name),
                        'usage_count': 1,
                        'is_active': True
                    }
                )
                
                # ノートブックに関連付け
                instance.tags.add(tag)
                
                # 使用回数をインクリメント（既存タグの場合）
                if not created:
                    tag.increment_usage()
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"タグ処理エラー: {e}", exc_info=True)
            raise forms.ValidationError(f'タグの処理中にエラーが発生しました: {str(e)}')
    
    def _handle_sub_notebooks(self, instance):
        """サブノートの作成・更新処理"""
        try:
            sub_notebooks_data = self.cleaned_data.get('sub_notebooks_json', [])
            
            # 既存のサブノートを削除（編集時）
            if self.instance.pk:
                instance.sub_notebooks.all().delete()
            
            # 新しいサブノートを作成
            for order, sub_notebook in enumerate(sub_notebooks_data):
                if isinstance(sub_notebook, str):
                    SubNotebook.objects.create(
                        notebook=instance,
                        title=sub_notebook,
                        order=order
                    )
                elif isinstance(sub_notebook, dict):
                    SubNotebook.objects.create(
                        notebook=instance,
                        title=sub_notebook['title'],
                        description=sub_notebook.get('description', ''),
                        order=order
                    )
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"サブノート処理エラー: {e}", exc_info=True)
            raise forms.ValidationError(f'サブノートの処理中にエラーが発生しました: {str(e)}')
    
    def _determine_tag_category(self, tag_name):
        """タグ名からカテゴリを自動判定（既存メソッドを使用）"""
        tag_lower = tag_name.lower()
        
        # テーマ関連キーワード
        theme_keywords = ['高配当', '成長株', 'グロース', 'バリュー', 'ポートフォリオ', 'ウォッチ']
        if any(keyword in tag_lower for keyword in theme_keywords):
            return 'STRATEGY'
        
        # 銘柄コードパターン
        import re
        if re.match(r'#\d{4}', tag_name):
            return 'STOCK'
        
        # 業界セクターキーワード
        sector_keywords = ['自動車', 'it', 'テクノロジー', '金融', '不動産', '製造', 'ヘルスケア']
        if any(keyword in tag_lower for keyword in sector_keywords):
            return 'SECTOR'
        
        return 'STRATEGY'
    
    def _generate_tag_description(self, tag_name):
        """タグ名から自動的に説明文を生成"""
        category = self._determine_tag_category(tag_name)
        
        category_descriptions = {
            'STOCK': f'{tag_name}の銘柄タグ',
            'STRATEGY': f'{tag_name}投資戦略',
            'SECTOR': f'{tag_name}業界セクター',
        }
        
        return category_descriptions.get(category, f'{tag_name}に関するタグ')


class EntryForm(forms.ModelForm):
    """エントリー作成・編集フォーム（銘柄情報付き）"""
    
    selected_tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='タグ'
    )
    
    # エントリータイプ固有フィールド（Ajax送信用）
    content = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = Entry
        fields = [
            'entry_type', 'title', 'stock_code', 'company_name', 'market',
            'event_date', 'is_important', 'is_bookmarked', 'sub_notebook'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'エントリーのタイトルを入力',
                'required': True
            }),
            'entry_type': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'stock_code': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 7203'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: トヨタ自動車'
            }),
            'market': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 東証プライム'
            }),
            'event_date': forms.DateInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'sub_notebook': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.notebook = kwargs.pop('notebook', None)
        super().__init__(*args, **kwargs)
        
        # サブノートの選択肢を設定
        if self.notebook:
            self.fields['sub_notebook'].queryset = SubNotebook.objects.filter(notebook=self.notebook)
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
    
    def clean_content(self):
        """コンテンツのJSONバリデーション"""
        content_json = self.cleaned_data.get('content', '{}')
        try:
            validate_json_content(content_json)
            return json.loads(content_json)
        except (json.JSONDecodeError, ValidationError):
            return {}
    
    def save(self, commit=True):
        """保存処理でタグを関連付け"""
        instance = super().save(commit=False)
        
        # コンテンツをJSONとして保存
        instance.content = self.cleaned_data.get('content', {})
        
        if commit:
            instance.save()
            
            # タグを関連付け
            selected_tags = self.cleaned_data.get('selected_tags')
            if selected_tags:
                instance.tags.set(selected_tags)
                for tag in selected_tags:
                    tag.increment_usage()
        
        return instance


class SubNotebookForm(forms.ModelForm):
    """サブノート作成・編集フォーム"""
    
    class Meta:
        model = SubNotebook
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 日本株'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'サブノートの説明（任意）'
            }),
        }


class NotebookSearchForm(forms.Form):
    """ノートブック検索フォーム"""
    
    q = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'ノート名、戦略、内容で検索...',
            'autocomplete': 'off'
        }),
        label='検索'
    )
    
    notebook_type = forms.ChoiceField(
        choices=[('', 'すべてのタイプ')] + Notebook.NOTEBOOK_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='ノートタイプ'
    )
    
    status = forms.ChoiceField(
        choices=[('', 'すべてのステータス')] + Notebook.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='ステータス'
    )
    
    is_favorite = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500'
        }),
        label='お気に入りのみ'
    )