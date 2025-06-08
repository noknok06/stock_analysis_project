# ========================================
# apps/accounts/forms.py
# ========================================

from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, AuthenticationForm, PasswordChangeForm
)
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.accounts.models import UserProfile, UserSettings
import re

class CustomUserCreationForm(UserCreationForm):
    """カスタムユーザー作成フォーム"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'メールアドレス'
        }),
        help_text='パスワードリセット等で使用します'
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '名前（任意）'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 共通スタイルの適用
        common_attrs = {
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        }
        
        self.fields['username'].widget.attrs.update({
            **common_attrs,
            'placeholder': 'ユーザー名'
        })
        self.fields['password1'].widget.attrs.update({
            **common_attrs,
            'placeholder': 'パスワード'
        })
        self.fields['password2'].widget.attrs.update({
            **common_attrs,
            'placeholder': 'パスワード（確認）'
        })
        
        # ヘルプテキストをカスタマイズ
        self.fields['username'].help_text = '3-150文字。英数字と@/./+/-/_のみ使用可能'
        self.fields['password1'].help_text = '8文字以上で、一般的すぎないパスワードを設定してください'
        self.fields['password2'].help_text = '確認のため、上記と同じパスワードを入力してください'
    
    def clean_username(self):
        """ユーザー名のカスタムバリデーション"""
        username = self.cleaned_data.get('username')
        
        if len(username) < 3:
            raise ValidationError('ユーザー名は3文字以上で入力してください。')
        
        # 日本語文字のチェック
        if re.search(r'[ひらがなカタカナ漢字]', username):
            raise ValidationError('ユーザー名に日本語文字は使用できません。')
        
        # 予約語チェック
        reserved_words = ['admin', 'api', 'www', 'mail', 'ftp', 'root', 'test']
        if username.lower() in reserved_words:
            raise ValidationError('このユーザー名は使用できません。')
        
        return username
    
    def clean_email(self):
        """メールアドレスの重複チェック"""
        email = self.cleaned_data.get('email')
        
        if User.objects.filter(email=email).exists():
            raise ValidationError('このメールアドレスは既に登録されています。')
        
        return email
    
    def save(self, commit=True):
        """ユーザー作成時の追加処理"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        
        if commit:
            user.save()
        
        return user


class CustomLoginForm(AuthenticationForm):
    """カスタムログインフォーム"""
    
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500'
        }),
        label='ログイン状態を保持する'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 共通スタイルの適用
        common_attrs = {
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        }
        
        self.fields['username'].widget.attrs.update({
            **common_attrs,
            'placeholder': 'ユーザー名またはメールアドレス',
            'autofocus': True
        })
        self.fields['password'].widget.attrs.update({
            **common_attrs,
            'placeholder': 'パスワード'
        })
    
    def clean_username(self):
        """ユーザー名またはメールアドレスでの認証を許可"""
        username = self.cleaned_data.get('username')
        
        # メールアドレス形式の場合、対応するユーザー名に変換
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        
        return username


class UserProfileForm(forms.ModelForm):
    """ユーザープロフィール編集フォーム"""
    
    class Meta:
        model = UserProfile
        fields = [
            'display_name', 'bio', 'investment_experience', 
            'investment_style', 'email_notifications', 'public_profile'
        ]
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '表示名（任意）'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': '投資経験や関心分野について簡単に紹介してください'
            }),
            'investment_experience': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'investment_style': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500'
            }),
            'public_profile': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500'
            }),
        }
    
    def clean_display_name(self):
        """表示名のバリデーション"""
        display_name = self.cleaned_data.get('display_name')
        
        if display_name and len(display_name) < 2:
            raise ValidationError('表示名は2文字以上で入力してください。')
        
        # 不適切な文字列チェック
        inappropriate_words = ['admin', 'moderator', 'system', 'test']
        if display_name and any(word in display_name.lower() for word in inappropriate_words):
            raise ValidationError('この表示名は使用できません。')
        
        return display_name


class UserSettingsForm(forms.ModelForm):
    """ユーザー設定フォーム"""
    
    class Meta:
        model = UserSettings
        fields = [
            'theme', 'language', 'items_per_page',
            'show_recent_activity', 'show_trending_tags', 'show_statistics',
            'price_alert_enabled', 'news_notification_enabled'
        ]
        widgets = {
            'theme': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'language': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'items_per_page': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '5',
                'max': '50'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # チェックボックスフィールドにスタイルを適用
        checkbox_fields = [
            'show_recent_activity', 'show_trending_tags', 'show_statistics',
            'price_alert_enabled', 'news_notification_enabled'
        ]
        
        for field_name in checkbox_fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'h-4 w-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500'
            })
    
    def clean_items_per_page(self):
        """ページング設定のバリデーション"""
        items_per_page = self.cleaned_data.get('items_per_page')
        
        if items_per_page < 5 or items_per_page > 50:
            raise ValidationError('表示件数は5-50の範囲で設定してください。')
        
        return items_per_page


class CustomPasswordChangeForm(PasswordChangeForm):
    """カスタムパスワード変更フォーム"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 共通スタイルの適用
        common_attrs = {
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        }
        
        self.fields['old_password'].widget.attrs.update({
            **common_attrs,
            'placeholder': '現在のパスワード'
        })
        self.fields['new_password1'].widget.attrs.update({
            **common_attrs,
            'placeholder': '新しいパスワード'
        })
        self.fields['new_password2'].widget.attrs.update({
            **common_attrs,
            'placeholder': '新しいパスワード（確認）'
        })
        
        # ラベルをカスタマイズ
        self.fields['old_password'].label = '現在のパスワード'
        self.fields['new_password1'].label = '新しいパスワード'
        self.fields['new_password2'].label = '新しいパスワード（確認）'


class AccountDeletionForm(forms.Form):
    """アカウント削除確認フォーム"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500',
            'placeholder': 'パスワードを入力して削除を確認'
        }),
        label='パスワード確認',
        help_text='アカウント削除を実行するために現在のパスワードを入力してください'
    )
    
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-red-600 bg-gray-700 border-gray-600 rounded focus:ring-red-500'
        }),
        label='削除を実行することを理解しています',
        help_text='この操作は取り消せません。すべてのデータが完全に削除されます。'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        """パスワードの確認"""
        password = self.cleaned_data.get('password')
        
        if not self.user.check_password(password):
            raise ValidationError('パスワードが正しくありません。')
        
        return password


class UserSearchForm(forms.Form):
    """ユーザー検索フォーム（管理者用）"""
    
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'ユーザー名、メールアドレスで検索...'
        }),
        label='検索'
    )
    
    investment_experience = forms.ChoiceField(
        choices=[('', 'すべて')] + UserProfile.INVESTMENT_EXPERIENCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='投資経験'
    )
    
    is_active = forms.ChoiceField(
        choices=[('', 'すべて'), ('true', 'アクティブ'), ('false', '非アクティブ')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='ステータス'
    )