# ========================================
# apps/notes/forms.py
# ========================================

from django import forms
from django.core.exceptions import ValidationError
from apps.notes.models import Notebook, Entry
from apps.tags.models import Tag
from apps.common.validators import validate_stock_code

class NotebookForm(forms.ModelForm):
    """ノートブック作成・編集フォーム"""
    
    # タグ選択用の追加フィールド
    selected_tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='タグ'
    )
    
    class Meta:
        model = Notebook
        fields = [
            'title', 'subtitle', 'stock_code', 'company_name',
            'target_price', 'sell_timing', 'investment_reason',
            'key_points', 'risk_factors', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: 7203 トヨタ自動車'
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: 長期保有・配当重視'
            }),
            'stock_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: 7203'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: トヨタ自動車'
            }),
            'investment_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'なぜこの銘柄に投資するのか、戦略を記述してください'
            }),
            'target_price': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: 3,200円'
            }),
            'sell_timing': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '例: 配当利回り3%を下回った時点'
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
    
    def save(self, commit=True):
        """保存処理でタグを関連付け"""
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # タグを関連付け
            selected_tags = self.cleaned_data.get('selected_tags')
            if selected_tags:
                instance.tags.set(selected_tags)
                # タグの使用回数を更新
                for tag in selected_tags:
                    tag.increment_usage()
        return instance


class EntryForm(forms.ModelForm):
    """エントリー作成・編集フォーム"""
    
    selected_tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='タグ'
    )
    
    class Meta:
        model = Entry
        fields = ['entry_type', 'title', 'content', 'selected_tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'エントリーのタイトルを入力'
            }),
            'entry_type': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'エントリーの内容をJSON形式で入力'
            }),
        }
    
    def save(self, commit=True):
        """保存処理でタグを関連付け"""
        instance = super().save(commit=False)
        if commit:
            instance.save()
            selected_tags = self.cleaned_data.get('selected_tags')
            if selected_tags:
                instance.tags.set(selected_tags)


class SearchForm(forms.Form):
    """検索フォーム"""
    
    q = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '銘柄名、タグ、分析内容で検索...',
            'autocomplete': 'off'
        }),
        label='検索'
    )
    
    entry_type = forms.ChoiceField(
        choices=[('', 'すべて')] + Entry.ENTRY_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='エントリータイプ'
    )
    
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='タグ'
    )