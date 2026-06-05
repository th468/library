from core.views.mixins import LibStatusMixin, PageTitleMixin, SearchMixin, StaffManagerMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import (
    DetailView,
    ListView,
    TemplateView,
)

from .models import Biblio, Favorite

# region __公開用ビュー（ユーザー向け）__

# #蔵書検索一覧
class BiblioSearchListView(LibStatusMixin, PageTitleMixin, SearchMixin, ListView):
    model = Biblio
    template_name = "catalog/book_list.html"
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
class BiblioDetailView(LoginRequiredMixin, LibStatusMixin, PageTitleMixin, DetailView):
    model = Biblio
    template_name = "catalog/book_detail.html"
    context_object_name = "biblio"
    page_title = "書籍詳細"

    def get_queryset(self):
        # 詳細画面でも在庫(books)と所在を効率よく取得
        return super().get_queryset().prefetch_related("categories", "books__shelf__floor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # セッションから表示モードを取得し、同時に削除
        context["reveal_mode"] = self.request.session.pop("reveal_mode", None)
        return context


# #お気に入り登録/解除（トグル）
class FavoriteToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        biblio = get_object_or_404(Biblio, pk=pk)
        favorite, created = Favorite.objects.get_or_create(user=request.user, biblio=biblio)

        if not created:
            # 既にお気に入り登録されていた場合は解除
            favorite.delete()
            messages.info(request, f"「{biblio.title}」をお気に入りから解除しました。")
        else:
            messages.success(request, f"「{biblio.title}」をお気に入りに登録しました！")

        # 遷移前のページに戻る（詳細画面など）
        return redirect(request.META.get("HTTP_REFERER", biblio.get_absolute_url()))


# endregion


# region __管理用ビュー（スタッフ向け）__

class ManageIndexView(StaffManagerMixin, PageTitleMixin, TemplateView):
    """
    管理者用ポータル画面
    ここから Django Admin や、将来的な高度な統計画面へ誘導する
    """
    template_name = "catalog/manage_index.html"
    page_title = "管理業務メニュー"

# endregion
