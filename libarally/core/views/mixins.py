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
        query = self.request.GET.get("q")
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
