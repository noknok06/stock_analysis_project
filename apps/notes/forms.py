# ========================================
# apps/notes/forms.py
# ========================================

import json
from django import forms
from django.core.exceptions import ValidationError
from apps.notes.models import Notebook, Entry
from apps.tags.models import Tag
from apps.common.validators import validate_stock_code, validate_json_content

class NotebookForm(forms.ModelForm):
    """ノートブック作成・編集フォーム"""
    
    # タグ選択用の追加フィールド
    selected_tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='タグ'
    )
    
    # JSON配列フィールド（フロントエンドから送信される）
    key_points = forms.CharField(required=False, widget=forms.HiddenInput())
    risk_factors = forms.CharField(required=False, widget=forms.HiddenInput())
    tag_changes = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = Notebook
        fields = [
            'title', 'subtitle', 'stock_code', 'company_name',
            'target_price', 'sell_timing', 'investment_reason',
            'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 7203 トヨタ自動車'
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 長期保有・配当重視'
            }),
            'stock_code': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 7203'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: トヨタ自動車'
            }),
            'investment_reason': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'なぜこの銘柄に投資するのか、戦略を記述してください'
            }),
            'target_price': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 3,200円'
            }),
            'sell_timing': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': '例: 配当利回り3%を下回った時点'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }
    
    def clean_stock_code(self):
        """銘柄コードのバリデーション"""
        stock_code = self.cleaned_data.get('stock_code')
        if stock_code:
            try:
                validate_stock_code(stock_code)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
        return stock_code
    
    def clean_key_points(self):
        """注目ポイントのJSONバリデーション"""
        key_points_json = self.cleaned_data.get('key_points', '[]')
        try:
            key_points = json.loads(key_points_json)
            if not isinstance(key_points, list):
                raise ValidationError('注目ポイントは配列形式である必要があります')
            return [point.strip() for point in key_points if point.strip()]
        except (json.JSONDecodeError, TypeError):
            return []
    
    def clean_risk_factors(self):
        """リスク要因のJSONバリデーション"""
        risk_factors_json = self.cleaned_data.get('risk_factors', '[]')
        try:
            risk_factors = json.loads(risk_factors_json)
            if not isinstance(risk_factors, list):
                raise ValidationError('リスク要因は配列形式である必要があります')
            return [factor.strip() for factor in risk_factors if factor.strip()]
        except (json.JSONDecodeError, TypeError):
            return []
    
    def clean_tag_changes(self):
        """タグ変更のJSONバリデーション"""
        tag_changes_json = self.cleaned_data.get('tag_changes', '{}')
        try:
            tag_changes = json.loads(tag_changes_json)
            if not isinstance(tag_changes, dict):
                raise ValidationError('タグ変更は辞書形式である必要があります')
            return tag_changes
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def save(self, commit=True):
        """保存処理でタグと配列フィールドを処理"""
        instance = super().save(commit=False)
        
        # JSON配列フィールドを保存
        instance.key_points = self.cleaned_data.get('key_points', [])
        instance.risk_factors = self.cleaned_data.get('risk_factors', [])
        
        if commit:
            instance.save()
            
            # タグの処理
            self._handle_tags(instance)
            
            # 選択されたタグも処理
            selected_tags = self.cleaned_data.get('selected_tags')
            if selected_tags:
                for tag in selected_tags:
                    instance.tags.add(tag)
                    tag.increment_usage()
        
        return instance
    
    def _handle_tags(self, instance):
        """タグの追加・削除処理"""
        tag_changes = self.cleaned_data.get('tag_changes', {})
        
        # 新しいタグを追加
        for tag_name in tag_changes.get('added', []):
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={
                    'category': 'STOCK' if tag_name.startswith('#') and any(c.isdigit() for c in tag_name[:5]) else 'STRATEGY',
                    'usage_count': 1
                }
            )
            instance.tags.add(tag)
            if not created:
                tag.increment_usage()
        
        # タグを削除
        for tag_id in tag_changes.get('removed', []):
            try:
                tag = Tag.objects.get(pk=tag_id)
                instance.tags.remove(tag)
            except Tag.DoesNotExist:
                pass


class EntryForm(forms.ModelForm):
    """エントリー作成・編集フォーム"""
    
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
        fields = ['entry_type', 'title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'エントリーのタイトルを入力'
            }),
            'entry_type': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }
    
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


class SearchForm(forms.Form):
    """検索フォーム"""
    
    q = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '銘柄名、タグ、分析内容で検索...',
            'autocomplete': 'off'
        }),
        label='検索'
    )
    
    entry_type = forms.ChoiceField(
        choices=[('', 'すべて')] + Entry.ENTRY_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='エントリータイプ'
    )
    
    status = forms.ChoiceField(
        choices=[('', 'すべて')] + Notebook.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='ステータス'
    )
    
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'text-white'
        }),
        label='タグ'
    )


class EntryAnalysisForm(forms.Form):
    """決算分析エントリー用フォーム"""
    
    summary = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': '決算の概要を記述してください'
        }),
        required=False,
        label='サマリー'
    )
    
    revenue = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '例: 8.7兆円 (+8.2%)'
        }),
        required=False,
        label='売上高'
    )
    
    operating_profit = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '例: 2.1兆円 (+12.1%)'
        }),
        required=False,
        label='営業利益'
    )
    
    net_income = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '例: 1.8兆円 (+15.3%)'
        }),
        required=False,
        label='純利益'
    )
    
    eps = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '例: 285円'
        }),
        required=False,
        label='EPS'
    )
    
    analysis = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 4,
            'placeholder': '決算内容の詳細分析を記述してください'
        }),
        required=False,
        label='分析'
    )
    
    outlook = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': '今後の業績見通しや予想を記述してください'
        }),
        required=False,
        label='今後の見通し'
    )


class EntryCalculationForm(forms.Form):
    """計算結果エントリー用フォーム"""
    
    current_price = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '例: 2,850円'
        }),
        required=False,
        label='現在株価'
    )
    
    per = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '例: 12.5倍'
        }),
        required=False,
        label='PER'
    )
    
    pbr = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '例: 1.1倍'
        }),
        required=False,
        label='PBR'
    )
    
    dividend_yield = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '例: 2.8%'
        }),
        required=False,
        label='配当利回り'
    )
    
    roe = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '例: 8.9%'
        }),
        required=False,
        label='ROE'
    )
    
    fair_value = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '例: 3,100円 - 3,300円'
        }),
        required=False,
        label='適正価格'
    )
    
    recommendation = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': '計算結果に基づく推奨や分析コメントを記述してください'
        }),
        required=False,
        label='推奨・コメント'
    )