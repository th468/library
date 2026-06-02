from django.contrib import admin
from .models import Biblio, Book, Category, Floor, Shelf

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'is_active')
    search_fields = ('name',)

class BookInline(admin.TabularInline):
    """
    書誌情報の詳細画面で、紐づく在庫（実体）を一覧表示・追加できるようにする
    """
    model = Book
    extra = 1
    fields = ('shelf', 'status', 'is_active')

@admin.register(Biblio)
class BiblioAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'total_count', 'available_count', 'is_active')
    list_filter = ('categories', 'is_active')
    search_fields = ('title', 'author', 'isbn')
    inlines = [BookInline]
    # ISBNで並び替え可能にする
    ordering = ('title',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('biblio_title', 'count', 'shelf', 'status', 'is_active')
    list_filter = ('status', 'shelf__floor', 'is_active')
    search_fields = ('biblio__title', 'biblio__isbn')
    
    def biblio_title(self, obj):
        return obj.biblio.title
    biblio_title.short_description = '書誌タイトル'

@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ('name', 'floor', 'is_active')
    list_filter = ('floor',)

@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
