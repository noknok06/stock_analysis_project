# ========================================
# apps/accounts/urls.py
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
    
    # パスワードリセット
    path('password/reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             success_url='/accounts/password/reset/done/'
         ), 
         name='password_reset'),
    
    path('password/reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password/reset/confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password/reset/complete/'
         ), 
         name='password_reset_confirm'),
    
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
    
    # ユーザー名重複チェック
    path('api/check-username/', views.check_username_ajax, name='check_username_ajax'),
    
    # プロフィール部分更新
    path('api/update-profile/', views.update_profile_ajax, name='update_profile_ajax'),
]