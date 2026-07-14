from django.contrib import admin
from django.utils import timezone

from core.admin import BaseLogicalDeleteAdmin

from .models import Lending, Reservation


@admin.register(Lending)
class LendingAdmin(BaseLogicalDeleteAdmin):
    """
    貸出情報の管理画面。
    user・book は貸出後の変更を防ぐため readonly とする。
    """

    # 一覧画面の設定
    list_display = (
        "__str__",
        "user",
        "status",
        "due_date",
        "return_date",
        "is_overdue_display",
        "is_active_display",
    )
    list_filter = (
        *BaseLogicalDeleteAdmin.list_filter,
        "status",
    )
    search_fields = ("user__email", "user__em_num", "book__biblio__title", "book__biblio__isbn")
    ordering = ("due_date",)
    # N+1解消: user / book / book の書誌・本棚を先読み
    list_select_related = ("user", "book__biblio", "book__shelf")

    # 編集画面の設定
    readonly_fields = (
        "user",       # 貸出後の利用者変更を禁止
        "book",       # 貸出後の書籍変更を禁止
        "created_at",
        "updated_at",
    )

    # 返却済みへの一括変更アクション
    actions = [*BaseLogicalDeleteAdmin.actions, "mark_as_returned"]

    @admin.display(description="延滞", boolean=True)
    def is_overdue_display(self, obj: Lending) -> bool:
        """延滞中かどうかを ✅/❌ アイコンで表示する"""
        return obj.is_overdue

    @admin.action(description="選択した貸出を返却済みにする（管理者操作）")
    def mark_as_returned(self, request, queryset):
        """
        管理者による一括返却処理。
        通常の collect() を経由せず直接 status を更新するため、
        Book.status の自動更新は行われない点に注意。
        あくまで記録上の修正用途として使用すること。
        """
        updated_count = queryset.filter(status=Lending.Status.LENDING).update(
            status=Lending.Status.RETURNED,
            return_date=timezone.now().date(),
        )
        self.message_user(request, f"{updated_count} 件の貸出を返却済みに更新しました。（Book.status は別途確認してください）")


@admin.register(Reservation)
class ReservationAdmin(BaseLogicalDeleteAdmin):
    """
    予約情報の管理画面。
    user・biblio は予約後の変更を防ぐため readonly とする。
    """

    # 一覧画面の設定
    list_display = (
        "__str__",
        "user",
        "biblio",
        "book",
        "status",
        "reserved_until",
        "is_active_display",
    )
    list_filter = (
        *BaseLogicalDeleteAdmin.list_filter,
        "status",
    )
    search_fields = ("user__email", "user__em_num", "biblio__title", "biblio__isbn")
    ordering = ("created_at",)
    # N+1解消: user / biblio / 引き当て済みの book を先読み
    list_select_related = ("user", "biblio", "book")

    # 編集画面の設定
    readonly_fields = (
        "user",     # 予約後の利用者変更を禁止
        "biblio",   # 予約後の書誌変更を禁止
        "created_at",
        "updated_at",
    )
