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

    def ongoing(self):
        """現在貸出中のもの（返却されていないもの）を返す"""
        return self.filter(return_date__isnull=True)

    def returned(self):
        """返却済みのものを返す"""
        return self.filter(return_date__isnull=False)

    def overdue(self):
        """期限を過ぎている貸出データを返す"""
        return self.ongoing().filter(due_date__lt=timezone.now().date())

    def expiring_soon(self, days=3):
        """期限が近い（days日以内）貸出データを返す"""
        threshold = timezone.now().date() + timezone.timedelta(days=days)
        return self.ongoing().filter(due_date__lte=threshold)


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
            res = Reservation.objects.ready_for_pickup().filter(book=target_book).first()
            if res:
                if res.user != user:
                    raise ValidationError("この本は現在、他の予約者のために取り置き中です。")
                else:
                    # 自分自身が予約者の場合は、貸出実行前に予約を消化（完了）させる
                    Reservation.objects.complete_reservation(res)

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

            if not Reservation.objects.mark_as_ready(book):
                # 予約がない場合のみ、在庫ありに戻して保存する
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
            lending = self.ongoing().filter(book=book).first()
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
            # 蔵書の状態チェック（在庫あり、または予約中の場合のみ貸出可能）
            if self.book.status not in [self.book.Status.AVAILABLE, self.book.Status.RESERVED]:
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

    def ongoing(self):
        """有効な（入荷待ち、または準備完了）予約を返す"""
        return self.active().filter(status__in=[1, 2])  # 1: WAITING, 2: READY

    def waiting(self):
        """入荷待ちの予約のみを返す"""
        return self.ongoing().filter(status=1)

    def ready_for_pickup(self):
        """準備完了（取置中）の予約のみを返す"""
        return self.ongoing().filter(status=2)

    def has_waiting_for(self, biblio):
        """特定の書誌に待機者がいるか（高速判定）"""
        return self.waiting().filter(biblio=biblio).exists()

    def get_next_waiting_for(self, biblio):
        """特定の書誌を待っている最優先の予約者を1人取得"""
        return self.waiting().filter(biblio=biblio).first()

    def expired(self):
        """取置期限を過ぎている準備完了状態の予約を返す"""
        return self.ongoing().filter(status=2, reserved_until__lt=timezone.now().date())


class ReservationManager(BaseManager.from_queryset(ReservationQuerySet)):
    """
    予約ロジックを管理するマネージャー
    """

    def handle_expired_reservations(self):
        """
        期限切れの予約（取置期限を過ぎたもの）を一括でキャンセル処理する。
        引き当てられていた本は、自動的に次の予約者へ回るか、在庫に戻ります。
        """
        expired_res_list = self.expired()
        count = 0
        for res in expired_res_list:
            self.cancel_reservation(res, remark="取置期限切れによる自動キャンセル")
            count += 1
        return count

    def create_reservation(self, user, biblio):
        """
        予約を新規作成する
        """
        with transaction.atomic():
            # 1. バリデーション：既に同じ書誌を借りていないか
            from .models import Lending

            if Lending.objects.ongoing().filter(user=user, book__biblio=biblio).exists():
                raise ValidationError("現在貸出中の書籍を予約することはできません。")

            # 2. バリデーション：既に有効な予約を持っていないか
            if self.ongoing().filter(user=user, biblio=biblio).exists():
                raise ValidationError("既にこの本に有効な予約が入っています。")

            # 3. 予約データの作成（一旦 WAITING で作成・保存）
            reservation = self.model(user=user, biblio=biblio, status=1)  # WAITING
            reservation.full_clean()
            reservation.save()

            # 4. 在庫チェックと引き当ての委譲
            from books.models import Book

            available_book = (
                Book.objects.filter(biblio=biblio, status=Book.Status.AVAILABLE).select_for_update().first()
            )

            if available_book:
                # 共通メソッドを呼び出し。内部で自身の予約が最優先として選ばれる。
                self.mark_as_ready(available_book)
                # 自身の状態が更新された（READYになった）ことを反映
                reservation.refresh_from_db()

            return reservation


    def mark_as_ready(self, book):
        """
        指定された本を、待機中の最優先予約者に引き当てる。
        引き当てに成功したら True, 待機者がいなければ False を返す。
        """
        # ショートカットメソッドを使用して意図を明確化
        if not self.has_waiting_for(book.biblio):
            return False

        with transaction.atomic():
            from books.models import Book

            target_book = Book.objects.select_for_update().get(pk=book.pk)

            # ロック後に再度、最新の状態で待機者を特定
            target_res = self.get_next_waiting_for(target_book.biblio)

            if not target_res:
                return False

            # 本と予約の状態を更新
            target_book.status = Book.Status.RESERVED
            target_book.save(update_fields=["status", "updated_at"])

            period_days = getattr(settings, "RESERVATION_PERIOD_DAYS", 7)
            target_res.status = 2  # READY
            target_res.book = target_book
            target_res.reserved_until = timezone.now().date() + timezone.timedelta(days=period_days)
            target_res.save(update_fields=["status", "book", "reserved_until", "updated_at"])

            return True

    def complete_reservation(self, reservation, lent_book=None):
        """
        予約者が実際に本を借りた際、予約を完了状態にする。
        もし確保していた本と実際に借りた本が異なる場合、確保していた本を解放します。
        """
        with transaction.atomic():
            # もし「別の本」を取り置いていた場合は、その本を解放して次の人へ回す
            if reservation.status == 2 and reservation.book and reservation.book != lent_book:
                old_book = reservation.book
                if not self.mark_as_ready(old_book):
                    from books.models import Book

                    old_book.status = Book.Status.AVAILABLE
                    old_book.save(update_fields=["status", "updated_at"])

            reservation.status = 3  # COMPLETED
            reservation.save(update_fields=["status", "updated_at"])

    def cancel_reservation(self, reservation, remark=None):
        """
        予約をキャンセルする。もし READY 状態だった場合は本を解放する。
        """
        with transaction.atomic():
            was_ready = reservation.status == 2  # READY
            target_book = reservation.book

            reservation.status = 4  # CANCELED
            if remark:
                reservation.remarks = (reservation.remarks or "") + f"\n[キャンセル理由: {remark}]"
            reservation.save(update_fields=["status", "remarks", "updated_at"])

            # もし「準備完了（取置中）」だった場合は、本を解放して次の予約者へ
            if was_ready and target_book:
                if not self.mark_as_ready(target_book):
                    # 次の予約者がいない場合のみ、在庫ありに戻す
                    from books.models import Book

                    target_book.status = Book.Status.AVAILABLE
                    target_book.save(update_fields=["status", "updated_at"])


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

        if Lending.objects.ongoing().filter(user=self.user, book__biblio=self.biblio).exists():
            raise ValidationError("現在貸出中の書籍を予約することはできません。")

        # 2. 重複予約のチェック（既に「待ち」または「準備完了」の予約があるか）
        if self.status == self.Status.WAITING:
            duplicate = (
                self.__class__.objects.ongoing().filter(user=self.user, biblio=self.biblio).exclude(pk=self.pk).exists()
            )
            if duplicate:
                raise ValidationError("既にこの本に有効な予約が入っています。")


# endregion
