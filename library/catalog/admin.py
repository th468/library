from django.contrib import admin

from core.admin import BaseLogicalDeleteAdmin

from .models import Biblio, Book, Category, Favorite, Floor, Shelf


@admin.register(Category)
class CategoryAdmin(BaseLogicalDeleteAdmin):
    list_display = ("name", "is_active_display", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


class BookInline(admin.TabularInline):
    """
    書誌情報の詳細画面で、紐づく蔵書（現物）を一覧表示・追加できるようにする。
    count は自動採番のため readonly で表示する。
    """

    model = Book
    extra = 0  # 不要な空行を非表示
    fields = ("count", "shelf", "status", "is_active")
    readonly_fields = ("count",)
    show_change_link = True  # BookAdmin の詳細画面へのリンクを表示


@admin.register(Biblio)
class BiblioAdmin(BaseLogicalDeleteAdmin):
    list_display = ("title", "author", "isbn", "total_count", "available_count", "is_active_display")
    list_filter = (*BaseLogicalDeleteAdmin.list_filter, "categories")
    search_fields = ("title", "author", "isbn")
    inlines = [BookInline]
    ordering = ("title",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Book)
class BookAdmin(BaseLogicalDeleteAdmin):
    list_display = ("__str__", "count", "biblio_title", "shelf", "status", "is_active_display")
    list_filter = (*BaseLogicalDeleteAdmin.list_filter, "status", "shelf__floor")
    search_fields = ("biblio__title", "biblio__isbn")
    readonly_fields = ("count", "created_at", "updated_at")
    # N+1問題の解消: biblio と shelf(→floor) を先読み
    list_select_related = ("biblio", "shelf__floor")

    @admin.display(description="書誌タイトル", ordering="biblio__title")
    def biblio_title(self, obj: Book) -> str:
        return obj.biblio.title


@admin.register(Shelf)
class ShelfAdmin(BaseLogicalDeleteAdmin):
    list_display = ("name", "floor", "is_active_display")
    list_filter = (*BaseLogicalDeleteAdmin.list_filter, "floor")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Floor)
class FloorAdmin(BaseLogicalDeleteAdmin):
    list_display = ("name", "is_active_display")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Favorite)
class FavoriteAdmin(BaseLogicalDeleteAdmin):
    list_display = ("user", "biblio", "is_active_display")
    list_filter = (*BaseLogicalDeleteAdmin.list_filter,)
    search_fields = ("user__email", "biblio__title")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("user", "biblio")
