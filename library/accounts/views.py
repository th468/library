from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView
)
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import UserCreationForm, UserLoginForm, ProfileEditForm

User = get_user_model()


class UserLoginView(LoginView):
    """ログインビュー"""
    form_class = UserLoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy("dashboard:index")


class UserLogoutView(LogoutView):
    """ログアウトビュー"""
    next_page = "accounts:login"


class UserRegistrationView(CreateView):
    """ユーザー登録ビュー"""
    model = User
    form_class = UserCreationForm
    template_name = "accounts/registration.html"
    success_url = reverse_lazy("accounts:login")


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """プロフィール詳細ビュー"""
    model = User
    template_name = "accounts/profile_detail.html"
    context_object_name = "profile_user"

    def get_object(self, queryset=None):
        # ログイン中のユーザー自身を返す
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """プロフィール編集ビュー"""
    model = User
    form_class = ProfileEditForm
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("accounts:profile_detail")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_url"] = reverse_lazy("accounts:profile_detail")
        return context


class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """パスワード変更ビュー"""
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_url"] = reverse_lazy("accounts:profile_detail")
        return context


class UserPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    """パスワード変更完了ビュー"""
    template_name = "accounts/password_change_done.html"
