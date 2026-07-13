from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from core.admin import BaseLogicalDeleteAdmin

from .models import Department

User = get_user_model()


@admin.register(Department)
class DepartmentAdmin(BaseLogicalDeleteAdmin):
    list_display = ("name", "is_active_display", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Django 標準の UserAdmin を継承し、カスタムフィールドを追加する。
    パスワード変更フォームのハッシュ化処理を引き継ぐため、継承は必須。
    """

    # 一覧画面の設定
    list_display = ("em_num", "email", "name", "department", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "department")
    search_fields = ("em_num", "email", "name")
    ordering = ("em_num",)
    list_select_related = ("department",)  # N+1解消

    # 編集画面のフィールドセット（DjangoUserAdmin のデフォルトを上書き）
    fieldsets = (
        (None, {"fields": ("email", "em_num", "password")}),
        ("個人情報", {"fields": ("name", "department", "remarks")}),
        ("貸出設定", {"fields": ("lending_limit", "lending_period_days")}),
        ("権限", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("日時情報", {"fields": ("created_at", "updated_at", "last_login")}),
    )
    # 新規作成画面のフィールドセット
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "em_num", "name", "department", "password1", "password2"),
        }),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")
