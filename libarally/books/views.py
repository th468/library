from django.contrib.auth.mixins import LoginRequiredMixin
from core.views.mixins import PageTitleMixin, SearchMixin, StaffManagerMixin
from django.shortcuts import render
from django.views.generic import (
    DetailView,
    ListView,
    TemplateView,
)

from .models import Biblio, Book, Floor, Shelf


# region __公開用ビュー（ユーザー向け）__

# #蔵書検索一覧
class BiblioSearchListView(PageTitleMixin, SearchMixin, ListView):
    model = Biblio
    template_name = "books/book_list.html"
    context_object_name = "biblios"
    paginate_by = 12
    page_title = "蔵書をさがす"
    search_fields = ["title", "author", "isbn", "categories__name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(categories__id=category_id)

        sort = self.request.GET.get("sort", "-created_at")
        sort_map = {"title": "title", "author": "author", "newest": "-created_at"}
        order_by = sort_map.get(sort, "-created_at")

        return queryset.order_by(order_by).prefetch_related("categories", "books").distinct()


# #蔵書詳細
class BiblioDetailView(LoginRequiredMixin, PageTitleMixin, DetailView):
    model = Biblio
    template_name = "books/book_detail.html"
    context_object_name = "biblio"
    page_title = "書籍詳細"

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'categories',
            'books__shelf__floor'
        )

# endregion


# region __管理用ビュー（スタッフ向け）__

class ManageIndexView(StaffManagerMixin, PageTitleMixin, TemplateView):
    """
    管理者用ポータル画面
    ここから Django Admin や、将来的な高度な統計画面へ誘導する
    """
    template_name = "books/manage_index.html"
    page_title = "管理業務メニュー"

# endregion
