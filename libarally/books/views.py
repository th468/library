from django.contrib.auth.mixins import LoginRequiredMixin
from core.views.mixins import PageTitleMixin, SearchMixin, StaffManagerMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import BiblioForm
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
        # 詳細画面でも在庫(books)と所在を効率よく取得
        return super().get_queryset().prefetch_related(
            'categories',
            'books__shelf__floor'
        )


# endregion


# region __管理用ビュー（スタッフ向け）__

class ManageIndexView(TemplateView):
    template_name = "books/manage_index.html"

# 書誌情報一覧
class ManageBiblioListView(StaffManagerMixin, PageTitleMixin, SearchMixin, ListView):
    model = Biblio
    template_name = "books/generic_list.html"
    context_object_name = "object_list"
    paginate_by = 10
    page_title = "【管理】書誌一覧"
    search_fields = ["isbn", "title", "author"]


# 書誌情報詳細
class ManageBiblioDetailView(StaffManagerMixin, PageTitleMixin, DetailView):
    model = Biblio
    template_name = "books/generic_detail.html"
    page_title = "【管理】書誌詳細"


# 書誌情報登録
class BiblioCreateView(StaffManagerMixin, CreateView):
    model = Biblio
    form_class = BiblioForm
    template_name = "books/generic_form.html"
    success_url = reverse_lazy("books:manageindex")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "書誌情報登録"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context


# 書誌情報更新
class BiblioUpdateView(StaffManagerMixin, UpdateView):
    model = Biblio
    form_class = BiblioForm
    template_name = "books/generic_form.html"
    success_url = reverse_lazy("books:manageindex")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "書誌情報の編集"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context


# 書誌情報削除
class BiblioDeleteView(StaffManagerMixin, DeleteView):
    model = Biblio
    template_name = "books/delete_form.html"
    success_url = reverse_lazy("books:manageindex")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "書誌情報の削除"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context


# 本棚一覧
class ShelfListView(StaffManagerMixin, PageTitleMixin, SearchMixin, ListView):
    model = Shelf
    template_name = "books/generic_list.html"
    context_object_name = "object_list"
    paginate_by = 10
    page_title = "【管理】本棚一覧"
    search_fields = ["name", "floor__name"]


# 階情報一覧
class FloorListView(StaffManagerMixin, PageTitleMixin, SearchMixin, ListView):
    model = Floor
    template_name = "books/generic_list.html"
    context_object_name = "object_list"
    paginate_by = 10
    page_title = "【管理】フロア一覧"
    search_fields = ["name"]


# 階情報詳細
class FloorDetailView(StaffManagerMixin, PageTitleMixin, DetailView):
    model = Floor
    template_name = "books/generic_detail.html"
    page_title = "【管理】フロア詳細"


# endregion
