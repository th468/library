from books.models import Book
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from .models import Lending


# 抽象クラス
class BaseLendingView(LoginRequiredMixin, View):
    def get_success_url(self):
        # 処理後はマイページ（貸出中一覧）に戻る想定
        return redirect("accounts:dashboard")


class LendingUserPermissionMixin(UserPassesTestMixin):
    def test_func(self):
        lending = get_object_or_404(Lending, pk=self.kwargs["pk"])
        return self.request.user == lending.user or self.request.user.is_staff


# 貸出用ビュー
class LendView(BaseLendingView):
    def post(self, request, book_id, *args, **kwargs):
        book = get_object_or_404(Book, pk=book_id)
        try:
            Lending.objects.lend(book, request.user)

        except ValidationError as e:
            messages.error(request, e.message)

        return self.get_success_url()


# 返却用ビュー
class CollectView(LendingUserPermissionMixin, BaseLendingView):
    def post(self, request, pk, *args, **kwargs):
        lending = get_object_or_404(Lending, pk=pk)
        try:
            Lending.objects.collect(lending, request.user)

        except ValidationError as e:
            messages.error(request, e.message)

        return self.get_success_url()


# 期限延長用ビュー
class RenewView(LendingUserPermissionMixin, BaseLendingView):
    def post(self, request, pk, *args, **kwargs):
        lending = get_object_or_404(Lending, pk=pk)
        try:
            Lending.objects.renew(lending, request.user)

        except ValidationError as e:
            messages.error(request, e.message)

        return self.get_success_url()
