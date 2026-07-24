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
    """ユーザーの貸出状況（IDセット、オブジェクト辞書、予約状況）をコンテキストに提供する Mixin。"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            from transactions.models import Lending, Reservation

            # 貸出中の全データを一括取得 (Book, Biblio も結合してクエリを削減)
            lendings = list(Lending.objects.ongoing().filter(user=user).select_related("book__biblio"))

            # IDセットの作成
            biblio_ids = {lending.book.biblio_id for lending in lendings}
            book_ids = {lending.book_id for lending in lendings}

            # {book_id: lending_object} の辞書を作成（テンプレートでの逆引用）
            user_lendings = {lending.book_id: lending for lending in lendings}

            # N+1回避：貸出中の書誌に対して、待機中の予約があるか一括チェック
            biblios_with_reservations = set(
                Reservation.objects.waiting().filter(biblio_id__in=biblio_ids).values_list("biblio_id", flat=True)
            )
        else:
            biblio_ids = set()
            book_ids = set()
            user_lendings = {}
            biblios_with_reservations = set()

        context["user_lending_ids"] = biblio_ids
        context["user_lent_book_ids"] = book_ids
        context["user_lendings"] = user_lendings
        context["biblios_with_reservations"] = biblios_with_reservations
        return context


class ReservationContextMixin:
    """ユーザーが予約中の書誌IDをセット形式で取得する Mixin。"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            from transactions.models import Reservation

            reservation_ids = set(Reservation.objects.ongoing().filter(user=user).values_list("biblio_id", flat=True))
            ready_book_ids = set(
                Reservation.objects.ready_for_pickup().filter(user=user).values_list("book_id", flat=True)
            )
        else:
            reservation_ids = set()
            ready_book_ids = set()
        context["user_reservation_ids"] = reservation_ids
        context["user_ready_book_ids"] = ready_book_ids
        return context


class LibStatusMixin(FavoriteContextMixin, LendingContextMixin, ReservationContextMixin):
    """
    お気に入り、貸出、予約のステータスを一括で取得する統合 Mixin。
    単一の Mixin 継承で全ステータスを取得可能にする。
    """

    pass
