from core.views.mixins import PageTitleMixin, SearchMixin, StaffManagerMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import BiblioForm
from .models import Biblio, Book, Floor, Shelf

# region __個別のビュー__


def index(request):
    return render(request, "books/index.html")


# region __蔵書情報関連ビュー__


# #書籍一覧
class BookListView(PageTitleMixin, SearchMixin, ListView):
    model = Book
    template_name = "books/book_list.html"
    context_object_name = "books"
    ordering = ["-created_at"]
    paginate_by = 10
    page_title = "蔵書一覧"
    search_fields = ["biblio__title", "biblio__author", "biblio__isbn"]


# #詳細画面
class BookDetailView(PageTitleMixin, DetailView):
    model = Book
    template_name = "books/book_detail.html"
    context_object_name = "book"
    page_title = "蔵書詳細"


# 管理インデックス
class ManageIndexView(TemplateView):
    template_name = "books/manage_index.html"


# #蔵書情報登録
# class BookCreateView(StaffManagerMixin, CreateView):
#     model = Book
#     form_class = BookForm
#     template_name = "books/generic_form.html"
#     success_url = reverse_lazy("books:manageindex")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["title"] = "蔵書登録"
#         context["cancel_url"] = reverse_lazy("books:manageindex")
#         return context

# #蔵書情報更新
# class BookUpdateView(StaffManagerMixin, UpdateView):
#     model = Book
#     form_class = BookForm
#     template_name = "books/generic_form.html"
#     success_url = reverse_lazy("books:manageindex")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["title"] = "蔵書情報の編集"
#         context["cancel_url"] = reverse_lazy("books:manageindex")
#         return context

# #蔵書情報削除
# class BookDeleteView(StaffManagerMixin, DeleteView):
#     model = Book
#     template_name = "books/delete_form.html"
#     success_url = reverse_lazy("books:manageindex")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["title"] = "蔵書情報の削除"
#         context["cancel_url"] = reverse_lazy("books:manageindex")
#         return context

# # endregion

# region __書誌情報関連ビュー__


# 書誌情報一覧
class BiblioListView(PageTitleMixin, SearchMixin, ListView):
    model = Biblio
    template_name = "books/generic_list.html"
    context_object_name = "object_list"
    paginate_by = 10
    page_title = "書誌情報一覧"
    search_fields = ["isbn", "title", "author"]


# 書誌情報詳細
class BiblioDetailView(PageTitleMixin, DetailView):
    model = Biblio
    template_name = "books/generic_detail.html"
    page_title = "書誌情報詳細"


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


# endregion 書誌情報関連ビュー

# region __本棚関連ビュー__


# 本棚一覧
class ShelfListView(PageTitleMixin, SearchMixin, ListView):
    model = Shelf
    template_name = "books/generic_list.html"
    context_object_name = "object_list"
    paginate_by = 10
    page_title = "本棚一覧"
    search_fields = ["name", "floor__name"]


# endregion 本棚関連ビュー

# region __階情報関連ビュー__


# 階情報一覧
class FloorListView(PageTitleMixin, SearchMixin, ListView):
    model = Floor
    template_name = "books/generic_list.html"
    context_object_name = "object_list"
    paginate_by = 10
    page_title = "フロア一覧"
    search_fields = ["name"]


# 階情報詳細
class FloorDetailView(PageTitleMixin, DetailView):
    model = Floor
    template_name = "books/generic_detail.html"
    page_title = "フロア情報詳細"


# endregion 階情報関連ビュー
