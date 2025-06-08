# ========================================
# apps/notes/forms.py - 完全版 NotebookForm
# ========================================

import json
from django import forms
from django.core.exceptions import ValidationError
from apps.notes.models import Notebook, Entry
from apps.tags.models import Tag
from apps.common.validators import validate_stock_code, validate_json_content

class NotebookForm(forms.ModelForm):
    """ノートブック作成・編集フォーム（統一タグ管理対応）"""
    
    # JSON配列フィールド（フロントエンドから送信される）
    key_points = forms.CharField(required=False, widget=forms.HiddenInput())
    risk_factors = forms.CharField(required=False, widget=forms.HiddenInput())
    selected_tags_json = forms.CharField(required=False, widget=forms.HiddenInput())
    
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
                'placeholder': '例: 7203 トヨタ自動車',
                'required': True
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 長期保有・配当重視'
            }),
            'stock_code': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: 7203',
                'maxlength': '10'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '例: トヨタ自動車'
            }),
            'investment_reason': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'なぜこの銘柄に投資するのか、戦略を記述してください',
                'required': True
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
    
    def __init__(self, *args, **kwargs):
        """フォーム初期化"""
        super().__init__(*args, **kwargs)
        
        # 必須フィールドのラベルに * を追加
        self.fields['title'].label = 'ノートタイトル *'
        self.fields['investment_reason'].label = '投資理由・戦略 *'
        
        # ヘルプテキストの追加
        self.fields['stock_code'].help_text = '4桁の数字で入力（例: 7203）'
        self.fields['investment_reason'].help_text = 'なぜこの銘柄に投資するのか、どのような戦略で臨むのかを具体的に記述してください'
    
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
    
    def clean_investment_reason(self):
        """投資理由のバリデーション"""
        investment_reason = self.cleaned_data.get('investment_reason')
        if not investment_reason or not investment_reason.strip():
            raise forms.ValidationError('投資理由・戦略は必須です。')
        
        # 最小文字数チェック
        if len(investment_reason.strip()) < 10:
            raise forms.ValidationError('投資理由は10文字以上で入力してください。')
        
        return investment_reason.strip()
    
    def clean_target_price(self):
        """目標株価のバリデーション"""
        target_price = self.cleaned_data.get('target_price')
        if target_price and target_price.strip():
            # 数字・カンマ・円マークのみ許可
            import re
            if not re.match(r'^[\d,円\s]+$', target_price.strip()):
                raise forms.ValidationError('目標株価は数字、カンマ、円マークのみ使用できます。')
        return target_price
    
    def clean_key_points(self):
        """注目ポイントのJSONバリデーション"""
        key_points_json = self.cleaned_data.get('key_points', '[]')
        try:
            key_points = json.loads(key_points_json)
            if not isinstance(key_points, list):
                raise ValidationError('注目ポイントは配列形式である必要があります')
            
            # 空文字列・None・空白のみの要素を除去
            cleaned_points = []
            for point in key_points:
                if point and isinstance(point, str) and point.strip():
                    cleaned_points.append(point.strip())
            
            # 重複除去
            cleaned_points = list(dict.fromkeys(cleaned_points))
            
            return cleaned_points
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
    
    def clean(self):
        """フォーム全体のクロスバリデーション"""
        cleaned_data = super().clean()
        
        stock_code = cleaned_data.get('stock_code')
        company_name = cleaned_data.get('company_name')
        
        # 銘柄コードがある場合は企業名も推奨
        if stock_code and not company_name:
            self.add_error('company_name', '銘柄コードが入力されている場合は企業名も入力することを推奨します。')
        
        # タグ数の制限チェック
        tags_data = cleaned_data.get('selected_tags_json', {})
        selected_tags = tags_data.get('selected', [])
        if len(selected_tags) > 10:
            raise forms.ValidationError('タグは最大10個まで選択できます。')
        
        return cleaned_data
    
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
        
        return instance
    
    def _handle_tags(self, instance):
        """タグの追加・削除処理（DRY原則適用）"""
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
            # エラーログを出力（実際の環境では適切なロギングを使用）
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"タグ処理エラー: {e}", exc_info=True)
            
            # エラーをユーザーに通知
            raise forms.ValidationError(f'タグの処理中にエラーが発生しました: {str(e)}')
    
    def _determine_tag_category(self, tag_name):
        """タグ名からカテゴリを自動判定"""
        tag_lower = tag_name.lower()
        
        # 銘柄コードパターン（#7203トヨタ など）
        import re
        if re.match(r'#\d{4}', tag_name):
            return 'STOCK'
        
        # 投資スタイルキーワード
        style_keywords = ['高配当', '成長株', '割安株', '配当株', '優待', 'グロース', 'バリュー']
        if any(keyword in tag_lower for keyword in style_keywords):
            return 'STYLE'
        
        # 業界セクターキーワード
        sector_keywords = ['自動車', 'it', 'テクノロジー', '金融', '不動産', '製造', 'ヘルスケア', 
                          'エネルギー', '小売', '通信', '食品', '化学', '鉄鋼', '商社']
        if any(keyword in tag_lower for keyword in sector_keywords):
            return 'SECTOR'
        
        # 分析手法キーワード
        analysis_keywords = ['決算', 'バリュエーション', 'テクニカル', '分析', '競合', 'dcf', 
                           'ファンダメンタル', 'チャート', 'per', 'pbr', 'roe']
        if any(keyword in tag_lower for keyword in analysis_keywords):
            return 'ANALYSIS'
        
        # 戦略キーワード
        strategy_keywords = ['長期', '短期', '投資', '保有', '積立', '分散', '集中', 'スイング']
        if any(keyword in tag_lower for keyword in strategy_keywords):
            return 'STRATEGY'
        
        # 市場状況キーワード
        market_keywords = ['業績', '好調', '回復', '成長', '期待', '上場', '決算期', '増配']
        if any(keyword in tag_lower for keyword in market_keywords):
            return 'MARKET'
        
        # リスクキーワード
        risk_keywords = ['リスク', '要注意', '警戒', '競合', '為替', '規制', '景気', '原材料']
        if any(keyword in tag_lower for keyword in risk_keywords):
            return 'RISK'
        
        # デフォルトは戦略
        return 'STRATEGY'
    
    def _generate_tag_description(self, tag_name):
        """タグ名から自動的に説明文を生成"""
        category = self._determine_tag_category(tag_name)
        
        category_descriptions = {
            'STOCK': f'{tag_name}の銘柄タグ',
            'STYLE': f'{tag_name}投資スタイル',
            'SECTOR': f'{tag_name}業界セクター',
            'ANALYSIS': f'{tag_name}分析手法',
            'STRATEGY': f'{tag_name}投資戦略',
            'MARKET': f'{tag_name}市場状況',
            'RISK': f'{tag_name}リスク要因'
        }
        
        return category_descriptions.get(category, f'{tag_name}に関するタグ')


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
                'placeholder': 'エントリーのタイトルを入力',
                'required': True
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


# エントリータイプ固有フォーム（既存のまま保持）
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