# ========================================
# apps/accounts/views.py
# ========================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, 
    PasswordResetView, PasswordResetConfirmView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import UserProfile, UserSettings, LoginHistory
from apps.accounts.forms import (
    CustomUserCreationForm, CustomLoginForm, 
    UserProfileForm, UserSettingsForm, 
    CustomPasswordChangeForm
)

# ========================================
# 認証関連ビュー
# ========================================

class CustomLoginView(LoginView):
    """カスタムログインビュー"""
    template_name = 'accounts/login.html'
    form_class = CustomLoginForm
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """ログイン成功時の処理"""
        # ログイン履歴を記録
        user = form.get_user()
        ip_address = self.get_client_ip()
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        
        LoginHistory.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        # プロフィールの最終ログインIPを更新
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.last_login_ip = ip_address
        profile.save(update_fields=['last_login_ip'])
        
        messages.success(self.request, 'ログインしました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """ログイン失敗時の処理"""
        # 失敗ログを記録（ユーザー名が判明している場合）
        username = form.cleaned_data.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
                LoginHistory.objects.create(
                    user=user,
                    ip_address=self.get_client_ip(),
                    user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                    success=False
                )
            except User.DoesNotExist:
                pass
        
        messages.error(self.request, 'ログインに失敗しました。')
        return super().form_invalid(form)
    
    def get_client_ip(self):
        """クライアントIPアドレスを取得"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class CustomLogoutView(LogoutView):
    """カスタムログアウトビュー"""
    next_page = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, 'ログアウトしました。')
        return super().dispatch(request, *args, **kwargs)


class SignUpView(CreateView):
    """ユーザー登録ビュー（修正版）"""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('dashboard:index')
    
    def form_valid(self, form):
        """登録成功時の処理（修正版）"""
        try:
            with transaction.atomic():
                # ユーザー作成（signalsでUserProfileとUserSettingsが自動作成される）
                user = form.save()
                
                # プロフィールとセッティングが作成されるまで少し待つ
                # signalsで自動作成されるので、ここでは作成しない
                
                # 自動ログイン
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                authenticated_user = authenticate(username=username, password=password)
                
                if authenticated_user:
                    login(self.request, authenticated_user)
                    messages.success(self.request, f'アカウント「{username}」を作成しました。')
                else:
                    messages.warning(self.request, 'アカウントは作成されましたが、自動ログインに失敗しました。手動でログインしてください。')
                    return redirect('accounts:login')
        
        except IntegrityError as e:
            messages.error(self.request, 'アカウント作成中にエラーが発生しました。既に存在するユーザー名またはメールアドレスの可能性があります。')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'アカウント作成中に予期しないエラーが発生しました: {str(e)}')
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """登録失敗時の処理"""
        messages.error(self.request, 'アカウント作成に失敗しました。入力内容を確認してください。')
        return super().form_invalid(form)



# ========================================
# プロフィール管理ビュー
# ========================================

class ProfileDetailView(LoginRequiredMixin, DetailView):
    """プロフィール詳細ビュー"""
    model = UserProfile
    template_name = 'accounts/profile_detail.html'
    context_object_name = 'profile'
    
    def get_object(self):
        """現在のユーザーのプロフィールを取得"""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_context_data(self, **kwargs):
        """コンテキストデータを追加"""
        context = super().get_context_data(**kwargs)
        
        # 統計情報を更新
        self.object.update_statistics()
        
        # 最近のログイン履歴
        context['recent_logins'] = LoginHistory.objects.filter(
            user=self.request.user,
            success=True
        )[:5]
        
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """プロフィール編集ビュー"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        """現在のユーザーのプロフィールを取得"""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        """更新成功時の処理"""
        messages.success(self.request, 'プロフィールを更新しました。')
        return super().form_valid(form)


class SettingsUpdateView(LoginRequiredMixin, UpdateView):
    """設定編集ビュー"""
    model = UserSettings
    form_class = UserSettingsForm
    template_name = 'accounts/settings.html'
    success_url = reverse_lazy('accounts:settings')
    
    def get_object(self):
        """現在のユーザーの設定を取得"""
        settings, created = UserSettings.objects.get_or_create(user=self.request.user)
        return settings
    
    def form_valid(self, form):
        """更新成功時の処理"""
        messages.success(self.request, '設定を更新しました。')
        return super().form_valid(form)


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """パスワード変更ビュー"""
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:profile')
    
    def form_valid(self, form):
        """パスワード変更成功時の処理"""
        messages.success(self.request, 'パスワードを変更しました。')
        return super().form_valid(form)


# ========================================
# Ajax API ビュー
# ========================================
@require_GET
def check_username_ajax(request):
    """ユーザー名重複チェックAPI（修正版）"""
    try:
        username = request.GET.get('username', '').strip()
        
        # バリデーション
        if not username:
            return JsonResponse({
                'available': False, 
                'message': 'ユーザー名を入力してください'
            })
        
        if len(username) < 3:
            return JsonResponse({
                'available': False, 
                'message': 'ユーザー名は3文字以上で入力してください'
            })
        
        # 不正文字チェック
        import re
        if not re.match(r'^[a-zA-Z0-9@.+\-_]+$', username):
            return JsonResponse({
                'available': False, 
                'message': 'ユーザー名に使用できない文字が含まれています'
            })
        
        # 予約語チェック
        reserved_words = ['admin', 'api', 'www', 'mail', 'ftp', 'root', 'test', 'demo']
        if username.lower() in reserved_words:
            return JsonResponse({
                'available': False, 
                'message': 'このユーザー名は予約されています'
            })
        
        # 重複チェック
        from django.contrib.auth.models import User
        exists = User.objects.filter(username__iexact=username).exists()
        
        if exists:
            return JsonResponse({
                'available': False, 
                'message': 'このユーザー名は既に使用されています'
            })
        
        return JsonResponse({
            'available': True, 
            'message': 'このユーザー名は使用できます'
        })
        
    except Exception as e:
        logger.error(f"Username check error: {e}", exc_info=True)
        return JsonResponse({
            'available': False, 
            'message': '確認中にエラーが発生しました。しばらく後でお試しください。'
        }, status=500)


@login_required
def update_profile_ajax(request):
    """プロフィール部分更新API（修正版）"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'error': 'POSTメソッドが必要です'
        }, status=405)
    
    try:
        # Content-Typeの確認
        content_type = request.content_type
        
        if 'application/json' in content_type:
            data = json.loads(request.body)
        else:
            # フォームデータとしても受け付ける
            data = request.POST.dict()
        
        from apps.accounts.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # 更新可能なフィールドのみ処理
        allowed_fields = ['display_name', 'bio', 'investment_experience', 'investment_style']
        updated_fields = []
        
        for field in allowed_fields:
            if field in data:
                value = data[field]
                if hasattr(profile, field):
                    setattr(profile, field, value)
                    updated_fields.append(field)
        
        # 統計更新のアクション
        if data.get('action') == 'update_statistics':
            profile.update_statistics()
            updated_fields.append('statistics')
        
        if updated_fields:
            profile.save(update_fields=updated_fields + ['updated_at'])
            return JsonResponse({
                'success': True, 
                'message': 'プロフィールを更新しました',
                'updated_fields': updated_fields
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': '更新するデータがありません'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': '無効なJSONデータです'
        }, status=400)
    except Exception as e:
        logger.error(f"Profile update error: {e}", exc_info=True)
        return JsonResponse({
            'success': False, 
            'error': f'更新中にエラーが発生しました: {str(e)}'
        }, status=500)


# ========================================
# 開発用のテストAPI（オプション）
# ========================================

@require_GET
def test_api(request):
    """API接続テスト用エンドポイント"""
    return JsonResponse({
        'status': 'ok',
        'message': 'APIは正常に動作しています',
        'timestamp': timezone.now().isoformat(),
        'user': request.user.username if request.user.is_authenticated else 'anonymous'
    })
    
# ========================================
# ユーティリティビュー
# ========================================

@login_required
def account_deletion_view(request):
    """アカウント削除ビュー"""
    if request.method == 'POST':
        # パスワード確認
        password = request.POST.get('password')
        if not request.user.check_password(password):
            messages.error(request, 'パスワードが正しくありません。')
            return render(request, 'accounts/delete_account.html')
        
        # アカウント削除実行
        try:
            with transaction.atomic():
                username = request.user.username
                request.user.delete()
                logout(request)
                messages.success(request, f'アカウント「{username}」を削除しました。')
                return redirect('accounts:login')
        except Exception as e:
            messages.error(request, f'アカウント削除に失敗しました: {str(e)}')
    
    return render(request, 'accounts/delete_account.html')


def account_deleted_view(request):
    """アカウント削除完了ビュー"""
    return render(request, 'accounts/account_deleted.html')