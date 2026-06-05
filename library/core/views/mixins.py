from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q


class SearchMixin:
    """
    複数のフィールドに対して icontains 検索を行うための Mixin。
    search_fields: 検索対象のフィールド名のリスト（例: ['title', 'author']）。
    """

    search_fields = []

    def get_queryset(self):
        queryset = super().get_queryset()
        # .strip() を追加し、空白文字のみの入力を「検索なし」として扱う
        query = self.request.GET.get("q", "").strip()
        if query and self.search_fields:
            search_query = Q()
            for field in self.search_fields:
                search_query |= Q(**{f"{field}__icontains": query})
            return queryset.filter(search_query).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["search_placeholder"] = f"{', '.join(self.search_fields)}で検索..."
        return context


class PageTitleMixin:
    """ページタイトルを動的に管理するための Mixin。"""

    page_title = ""

    def get_page_title(self):
        """タイトルを動的に生成したい場合はオーバーライドする。"""
        query = self.request.GET.get("q", "").strip()
        if query and hasattr(self, "object_list"):
            return f"[{query}]の検索結果 [{self.object_list.count()}件]"
        return self.page_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.get_page_title()
        return context


class StaffManagerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """スタッフ権限を持つユーザーのみにアクセスを制限するための Mixin。"""

    raise_exception = True

    def test_func(self):
        return self.request.user.is_staff


class FavoriteContextMixin:
    """ユーザーのお気に入り書誌IDをセット形式で取得する Mixin。"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            from catalog.models import Favorite

            favorite_ids = set(Favorite.objects.filter(user=user).values_list("biblio_id", flat=True))
        else:
            favorite_ids = set()
        context["user_favorite_ids"] = favorite_ids
        return context


class LendingContextMixin:
    """ユーザーが貸出中の書誌IDおよび蔵書IDをセット形式で取得する Mixin。"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            from transactions.models import Lending

            # DBアクセスを1回に集約するため、タプル形式で一括取得
            ongoing_data = Lending.objects.ongoing().filter(user=user).values_list("book__biblio_id", "book_id")

            # Python側でそれぞれのIDセットに振り分け（メモリ上での高速処理）
            biblio_ids = {item[0] for item in ongoing_data}
            book_ids = {item[1] for item in ongoing_data}
        else:
            biblio_ids = set()
            book_ids = set()
        context["user_lending_ids"] = biblio_ids
        context["user_lent_book_ids"] = book_ids
        return context


class ReservationContextMixin:
    """ユーザーが予約中の書誌IDをセット形式で取得する Mixin。"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            from transactions.models import Reservation

            reservation_ids = set(Reservation.objects.ongoing().filter(user=user).values_list("biblio_id", flat=True))
        else:
            reservation_ids = set()
        context["user_reservation_ids"] = reservation_ids
        return context


class LibStatusMixin(FavoriteContextMixin, LendingContextMixin, ReservationContextMixin):
    """
    お気に入り、貸出、予約のステータスを一括で取得する統合 Mixin。
    単一の Mixin 継承で全ステータスを取得可能にする。
    """

    pass
