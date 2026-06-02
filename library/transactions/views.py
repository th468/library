from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View

from catalog.models import Biblio, Book
from .models import Lending, Reservation


# 貸出実行
class LendActionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        try:
            Lending.objects.lend(book, request.user)
            request.session["reveal_mode"] = "lend"
            messages.success(request, f"「{book.biblio.title}」の貸出手続きが完了しました。")
        except ValidationError as e:
            messages.error(request, e.message)

        # Book ID ではなく Biblio ID でリダイレクト
        return redirect(reverse("catalog:bookdetail", kwargs={"pk": book.biblio.pk}))


# 予約実行
class ReserveActionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        try:
            Reservation.objects.create_reservation(request.user, book.biblio)
            request.session["reveal_mode"] = "reserve"
            messages.success(request, f"「{book.biblio.title}」を予約しました。")
        except ValidationError as e:
            messages.error(request, e.message)

        # Book ID ではなく Biblio ID でリダイレクト
        return redirect(reverse("catalog:bookdetail", kwargs={"pk": book.biblio.pk}))


# 返却実行
class CollectActionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        # テンプレートからは Book ID が渡されるため、その本のアクティブな貸出を探す
        lending = get_object_or_404(Lending.objects.ongoing(), book__pk=pk, user=request.user)
        try:
            Lending.objects.collect(lending, request.user)
            messages.success(request, "返却が完了しました。")
        except ValidationError as e:
            messages.error(request, e.message)
        return redirect("dashboard:index")


# 延長実行
class RenewActionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        # テンプレートからは Book ID が渡されることを想定し、その本のアクティブな貸出を探す
        lending = get_object_or_404(Lending.objects.ongoing(), book__pk=pk, user=request.user)
        try:
            Lending.objects.renew(lending, request.user)
            messages.success(request, "貸出期間を延長しました。")
        except ValidationError as e:
            messages.error(request, e.message)
        return redirect("dashboard:index")


# 予約キャンセル実行
class ReservationCancelActionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from .models import Reservation

        reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
        try:
            Reservation.objects.cancel_reservation(reservation, remark="ユーザーによるキャンセル")
            messages.success(request, f"「{reservation.biblio.title}」の予約を取り消しました。")
        except ValidationError as e:
            messages.error(request, e.message)

        return redirect("dashboard:index")
