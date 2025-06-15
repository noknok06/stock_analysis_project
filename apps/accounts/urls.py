# ========================================
# apps/accounts/urls.py - 完全版
# ========================================

from django.urls import path
from django.contrib.auth import views as auth_views
from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    # ========================================
    # 認証関連URL
    # ========================================
    
    # ログイン・ログアウト
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # ユーザー登録
    path('signup/', views.SignUpView.as_view(), name='signup'),
    
    # パスワード変更
    path('password/change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html'
         ), 
         name='password_change_done'),
    
    # ========================================
    # パスワードリセット関連URL（完全版）
    # ========================================
    
    # パスワードリセット開始
    path('password/reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/accounts/password/reset/done/',
             from_email=None,  # settings.DEFAULT_FROM_EMAIL を使用
         ), 
         name='password_reset'),
    
    # パスワードリセット送信完了
    path('password/reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    # パスワードリセット確認（メールのリンクから）
    path('password/reset/confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password/reset/complete/'
         ), 
         name='password_reset_confirm'),
    
    # パスワードリセット完了
    path('password/reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # ========================================
    # プロフィール管理URL
    # ========================================
    
    # プロフィール表示・編集
    path('profile/', views.ProfileDetailView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    
    # 設定
    path('settings/', views.SettingsUpdateView.as_view(), name='settings'),
    
    # アカウント削除
    path('delete/', views.account_deletion_view, name='delete_account'),
    path('deleted/', views.account_deleted_view, name='account_deleted'),
    
    # ========================================
    # Ajax API URL
    # ========================================
    
    # ユーザー名重複チェック（認証不要）
    path('api/check-username/', views.check_username_ajax, name='check_username_ajax'),
    
    # プロフィール部分更新（認証必要）
    path('api/update-profile/', views.update_profile_ajax, name='update_profile_ajax'),
    
    # API接続テスト（開発用）
    path('api/test/', views.test_api, name='test_api'),
]