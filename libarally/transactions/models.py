from core.models.base import BaseManager, BaseModel, BaseQuerySet
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

# region 貸出管理機能


# 貸出情報検索用QuerySet
class LendingQuerySet(BaseQuerySet):
    """
    貸出データの検索を便利にするカスタムQuerySet
    """

    def active(self):
        """プロジェクト標準の有効フラグに加え、現在貸出中のもの（返却されていないもの）を返す"""
        return super().active().filter(return_date__isnull=True)

    def overdue(self):
        """期限を過ぎている貸出データを返す"""
        return self.active().filter(due_date__lt=timezone.now().date())


# 貸出情報用Manager
class LendingManager(BaseManager.from_queryset(LendingQuerySet)):
    def _get_locked_lending_and_book(self, lending_pk):
        """
        [共通処理] Lendingと紐づくBookをセットでロックして取得する。
        ※ロック順序を固定することでデッドロックを防止。
        """
        # 1. まずLendingをロック
        target_lending = self.select_for_update().get(pk=lending_pk)

        # 2. 次に紐づくBookをロック
        from books.models import Book

        target_book = Book.objects.select_for_update().get(pk=target_lending.book_id)

        return target_lending, target_book

    # 貸出処理
    def lend(self, book, user):
        # トランザクション開始、対象の書籍をロック
        with transaction.atomic():
            from books.models import Book

            target_book = Book.objects.select_for_update().get(pk=book.pk)

            # 予約チェックロジック
            from .models import Reservation

            # その本が「準備完了」かつ「予約者が自分以外」ならエラー
            res = Reservation.objects.active().filter(book=target_book, status=Reservation.Status.READY).first()
            if res and res.user != user:
                raise ValidationError("この本は現在、他の予約者のために取り置き中です。")

            # 貸出期限を計算
            calculated_due_date = timezone.now().date() + timezone.timedelta(days=user.lending_period_days)
            # インスタンスの生成、バリデーション
            lending = self.model(
                user=user,
                book=target_book,
                due_date=calculated_due_date,
            )
            lending.full_clean()

            target_book.status = target_book.Status.LENT
            target_book.save()

            lending.save()
            return lending

    # 返却処理
    def collect(self, lending, user):
        # トランザクション開始、対象の書籍をロック
        with transaction.atomic():
            lending, book = self._get_locked_lending_and_book(lending.pk)
            # バリデーション
            if lending.user != user and not user.is_staff:
                raise ValidationError("ログインユーザーはこの本を貸出していません。")

            if lending.status == self.model.Status.RETURNED:
                raise ValidationError("この本はすでに返却済みです。")

            # 貸出情報の更新
            lending.return_date = timezone.now().date()
            lending.status = self.model.Status.RETURNED
            lending.save(update_fields=["return_date", "status", "updated_at"])

            # 予約の引き当て
            from .models import Reservation

            next_res = Reservation.objects.waiting().filter(biblio=book.biblio).first()

            if next_res:
                # 予約がある場合：準備完了へ
                Reservation.objects.mark_as_ready(next_res, book)
                book.status = book.Status.RESERVED
            else:
                # 予約がない場合：通常通り利用可能へ
                book.status = book.Status.AVAILABLE

            book.save(update_fields=["status", "updated_at"])
            return lending

    # 貸出期間延長機能
    def renew(self, lending, user, days=14):
        with transaction.atomic():
            lending, book = self._get_locked_lending_and_book(lending.pk)

            # バリデーション
            if lending.user != user and not user.is_staff:
                raise ValidationError("ログインユーザーはこの本を貸出していません。")

            if lending.status != self.model.Status.LENDING:
                raise ValidationError("貸出中以外のレコードは延長できません。")

            if lending.is_overdue:
                raise ValidationError("期限が過ぎている本は延長できません。一度返却してください。")

            # 予約の有無を確認
            from .models import Reservation

            has_waiting_reservation = Reservation.objects.waiting().filter(biblio=book.biblio).exists()

            if has_waiting_reservation:
                raise ValidationError("この本には次に予約が入っているため、延長できません。")
            # 期間の更新
            lending.due_date += timezone.timedelta(days=days)
            lending.save(update_fields=["due_date", "updated_at"])

            return lending

    # 返却処理（書籍から逆引き）
    def collect_by_book(self, book, user):
        with transaction.atomic():
            # 貸出中のレコードを特定。存在しない場合は例外を投げる
            lending = self.active().filter(book=book).first()
            if not lending:
                raise ValidationError(f"「{book.title}」の有効な貸出レコードが見つかりません。")

            # 既存の collect メソッドに委譲（ここでロックとバリデーションが行われる）
            return self.collect(lending, user)


class Lending(BaseModel):
    class Status(models.IntegerChoices):
        LENDING = 1, "貸出中"
        RETURNED = 2, "返却済み"
        OTHER = 3, "その他、備考にて記入"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, verbose_name="利用者")
    book = models.ForeignKey("books.Book", on_delete=models.PROTECT, verbose_name="書籍")
    due_date = models.DateField("返却期限")
    return_date = models.DateField("返却日", null=True, blank=True)
    status = models.IntegerField("状況", choices=Status.choices, default=Status.LENDING, db_index=True)

    class Meta:
        verbose_name = "貸出情報"
        verbose_name_plural = "貸出情報"

    objects = LendingManager()

    def __str__(self):
        return f"【貸出】{self.book.biblio.title} (期限: {self.due_date})"

    @property
    def is_overdue(self):
        return self.status == self.Status.LENDING and self.due_date < timezone.now().date()

    @property
    def days_overdue(self):
        """延滞日数を返す（延滞していない場合は0）"""
        if self.is_overdue:
            delta = timezone.now().date() - self.due_date
            return delta.days
        return 0

    def clean(self):
        super().clean()

        # ガード句：材料が揃っていなければ即終了
        if not self.user_id or not self.book_id:
            return
        # 1. 新規登録時のみのチェック（self.pk がない ＝ まだ保存されていない）
        if not self.pk:
            # 蔵書の状態チェック
            if self.book.status != self.book.Status.AVAILABLE:
                raise ValidationError("この本は現在ご利用いただけません。")

            # ユーザーの上限チェック
            if not self.user.can_lend:
                raise ValidationError(f"貸出上限[{self.user.lending_limit}]件に達しています。")

            # 延滞チェック
            if self.user.has_overdue_loans:
                raise ValidationError("延滞中の書籍があるため、貸出できません。")


# endregion 貸出処理


# region 予約マネージャー
class ReservationQuerySet(BaseQuerySet):
    """
    予約データの検索を便利にするカスタムQuerySet
    """

    def active(self):
        """プロジェクト標準の有効フラグに加え、有効な（入荷待ち、または準備完了）予約を返す"""
        return super().active().filter(status__in=[1, 2])  # 1: WAITING, 2: READY

    def waiting(self):
        """入荷待ちの予約のみを返す"""
        return self.active().filter(status=1)

    def expired(self):
        """取置期限を過ぎている準備完了状態の予約を返す"""
        return self.active().filter(status=2, reserved_until__lt=timezone.now().date())


class ReservationManager(BaseManager.from_queryset(ReservationQuerySet)):
    """
    予約ロジックを管理するマネージャー
    """

    def create_reservation(self, user, biblio):
        """
        予約を新規作成する
        """
        with transaction.atomic():
            # 1. バリデーション：既に同じ書誌を借りていないか
            from .models import Lending

            if Lending.objects.active().filter(user=user, book__biblio=biblio).exists():
                raise ValidationError("現在貸出中の書籍を予約することはできません。")

            # 2. バリデーション：既に有効な予約を持っていないか
            if self.active().filter(user=user, biblio=biblio).exists():
                raise ValidationError("既にこの本に有効な予約が入っています。")

            # 予約作成
            reservation = self.model(user=user, biblio=biblio, status=1)  # WAITING
            reservation.full_clean()
            reservation.save()
            return reservation

    def mark_as_ready(self, reservation, book):
        """
        本が返却された際などに、予約を「準備完了（取置中）」にする
        """
        with transaction.atomic():
            # 書籍をロック
            from books.models import Book

            target_book = Book.objects.select_for_update().get(pk=book.pk)

            # settings.pyから取置期間を取得（デフォルト7日）
            period_days = getattr(settings, "RESERVATION_PERIOD_DAYS", 7)

            reservation.status = 2  # READY
            reservation.book = target_book
            reservation.reserved_until = timezone.now().date() + timezone.timedelta(days=period_days)

            reservation.save(update_fields=["status", "book", "reserved_until", "updated_at"])
            return reservation

    def complete_reservation(self, reservation):
        """
        予約者が実際に本を借りた際、予約を完了状態にする
        """
        reservation.status = 3  # COMPLETED
        reservation.is_active = False
        reservation.save(update_fields=["status", "is_active", "updated_at"])

    def cancel_reservation(self, reservation, remark=None):
        """
        予約をキャンセルする
        """
        reservation.status = 4  # CANCELED
        reservation.is_active = False
        if remark:
            reservation.remarks = (reservation.remarks or "") + f"\n[キャンセル理由: {remark}]"
        reservation.save(update_fields=["status", "is_active", "remarks", "updated_at"])


# endregion


# 予約関連モデル
class Reservation(BaseModel):
    class Status(models.IntegerChoices):
        WAITING = 1, "入荷待ち"  # 書籍がすべて貸出中で、返却を待っている状態
        READY = 2, "準備完了（取置中）"  # 本が確保され、カウンターで受け取りを待っている状態
        COMPLETED = 3, "貸出済み"  # 予約していた本が実際に貸し出された状態
        CANCELED = 4, "キャンセル"  # ユーザーまたはスタッフによる取り消し
        EXPIRED = 5, "期限切れ"  # 取置期限（reserved_until）を過ぎた状態

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        verbose_name="利用者",
    )
    biblio = models.ForeignKey(
        "books.Biblio",
        on_delete=models.PROTECT,
        verbose_name="予約書誌",
    )
    # 予約時点では特定の「本（個体）」は決まっていないため、null=Trueとする
    book = models.ForeignKey(
        "books.Book",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="予約書籍",
    )

    status = models.IntegerField("予約状況", choices=Status.choices, default=Status.WAITING, db_index=True)
    reserved_until = models.DateField("取置期限", null=True, blank=True)

    objects = ReservationManager()

    class Meta:
        verbose_name = "予約情報"
        verbose_name_plural = "予約情報"
        ordering = ["created_at"]  # 先着順に処理するための設定

    def __str__(self):
        return f"【予約】{self.biblio.title} (状況: {self.get_status_display()})"

    def clean(self):
        super().clean()

        # user が None の場合は、以降の user.can_lend チェックをスキップする
        # (user 自体の必須チェックは Django の基本バリデーションが別途行うため)
        if not self.user_id or not self.biblio_id:
            return
        # 1. 既に同じ本を借りている場合は予約できない
        from .models import Lending

        if Lending.objects.active().filter(user=self.user, book__biblio=self.biblio).exists():
            raise ValidationError("現在貸出中の書籍を予約することはできません。")

        # 2. 重複予約のチェック（既に「待ち」または「準備完了」の予約があるか）
        if self.status == self.Status.WAITING:
            duplicate = (
                self.__class__.objects.active().filter(user=self.user, biblio=self.biblio).exclude(pk=self.pk).exists()
            )
            if duplicate:
                raise ValidationError("既にこの本に有効な予約が入っています。")


# endregion
