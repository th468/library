from core.views.mixins import LibStatusMixin, PageTitleMixin, SearchMixin, StaffManagerMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import (
    DetailView,
    ListView,
    TemplateView,
)
from transactions.models import Lending, Reservation

from .models import Biblio, Favorite, Shelf

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

    def get_page_title(self):
        query = self.request.GET.get("q", "").strip()
        category_id = self.request.GET.get("category")

        # カテゴリ名の取得
        category_name = ""
        if category_id:
            from .models import Category

            category = Category.objects.filter(id=category_id).first()
            if category:
                category_name = category.name

        # タイトルの組み立て
        if query and category_name:
            title = f"「{category_name}」内の「{query}」の検索結果"
        elif query:
            title = f"「{query}」の検索結果"
        elif category_name:
            title = f"カテゴリ：{category_name}"
        else:
            title = self.page_title

        # 件数の追加 (Paginationにかかわらず全件数を表示)
        if hasattr(self, "object_list"):
            count = self.get_queryset().count()
            title += f" ({count}件)"

        return title


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


# 本棚・フロア詳細（アクセス制限付き）
class ShelfDetailView(LoginRequiredMixin, PageTitleMixin, DetailView):
    model = Shelf
    template_name = "catalog/shelf_detail.html"
    context_object_name = "shelf"
    page_title = "本棚・フロア詳細"

    def get_queryset(self):
        # 関連する Floor 情報を効率的に取得するために select_related を使用
        return super().get_queryset().select_related("floor")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # アクセス制限: ログインユーザーが、この本棚にある本の「貸出中」または「準備完了の予約」を持っているかチェック
        user = request.user

        has_active_lending = Lending.objects.filter(
            user=user, book__shelf=self.object, status=Lending.Status.LENDING
        ).exists()

        has_active_reservation = Reservation.objects.filter(
            user=user, book__shelf=self.object, status=Reservation.Status.READY
        ).exists()

        if not (has_active_lending or has_active_reservation):
            raise PermissionDenied(
                "この本棚の所在情報にアクセスする権限がありません。"
                "所在情報は、貸出中または予約が準備完了になった後にのみ確認できます。"
            )

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


# #お気に入り登録/解除（トグル）
class FavoriteToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        biblio = get_object_or_404(Biblio, pk=pk)
        # 論理削除されたものも含めて全レコードから検索
        favorite = Favorite.all_objects.filter(user=request.user, biblio=biblio).first()

        if favorite:
            if favorite.is_active:
                # 有効な場合は解除（論理削除）
                favorite.delete()
                messages.info(request, f"「{biblio.title}」をお気に入りから解除しました。")
            else:
                # 無効な場合は再有効化
                favorite.is_active = True
                favorite.save()
                messages.success(request, f"「{biblio.title}」をお気に入りに登録しました！")
        else:
            # 存在しない場合は新規作成
            Favorite.objects.create(user=request.user, biblio=biblio)
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
