from accounts.factories import UserFactory
from books.factories import BiblioFactory, BookFactory
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from core.tests.test_mixins import BaseModelTestMixin
from ..factories import LendingFactory, ReservationFactory
from ..models import Lending, Reservation


class LendingManagerTest(TestCase):
    """
    LendingManagerの純粋なロジック（lend, collect, renew）をテストする
    ※Factoryを使わず、Managerメソッド経由で作成・操作する
    """

    def setUp(self):
        self.user = UserFactory(lending_period_days=14, lending_limit=5)
        self.biblio = BiblioFactory()
        self.book = BookFactory(biblio=self.biblio, status=1)  # AVAILABLE

    def test_lend_success(self):
        """lend: 正常に貸出が作成され、書籍のステータスがLENTに変わるか"""
        lending = Lending.objects.lend(self.book, self.user)
        self.assertEqual(lending.status, Lending.Status.LENDING)
        self.assertEqual(lending.due_date, timezone.now().date() + timezone.timedelta(days=14))
        self.book.refresh_from_db()
        self.assertEqual(self.book.status, 2)  # LENT

    def test_collect_success_no_reservation(self):
        """collect: 予約がない場合、返却後に書籍がAVAILABLEに戻るか"""
        lending = Lending.objects.lend(self.book, self.user)
        Lending.objects.collect(lending, self.user)
        self.book.refresh_from_db()
        self.assertEqual(self.book.status, 1)  # AVAILABLE

    def test_collect_and_trigger_reservation(self):
        """collect: 待機中の予約がある場合、返却後に書籍がRESERVEDになり予約がREADYになるか"""
        # 他のユーザーが同じ書誌を予約
        other_user = UserFactory()
        reservation = Reservation.objects.create_reservation(other_user, self.biblio)

        lending = Lending.objects.lend(self.book, self.user)
        Lending.objects.collect(lending, self.user)

        # 書籍が取り置き状態になっているか
        self.book.refresh_from_db()
        self.assertEqual(self.book.status, 3)

        # 予約がREADY(2)になっているか
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 2)
        self.assertEqual(reservation.book, self.book)

    def test_renew_success(self):
        """renew: 正常に期間が延長されるか"""
        lending = Lending.objects.lend(self.book, self.user)
        original_due = lending.due_date
        renewed = Lending.objects.renew(lending, self.user, days=7)
        self.assertEqual(renewed.due_date, original_due + timezone.timedelta(days=7))


class LendingModelTest(TestCase, BaseModelTestMixin):
    """
    Lendingモデルの定義とプロパティの振る舞いをテストする
    """

    factory_class = LendingFactory

    def run_str_test(self):
        """__str__ の独自形式（【貸出】）を検証"""
        lending = LendingFactory()
        display_str = str(lending)
        self.assertIn("【貸出】", display_str)

    def test_required_fields(self):
        lending = LendingFactory()
        lending.user = None
        with self.assertRaises(ValidationError):
            lending.full_clean()

    # ② 個別テスト項目
    def test_is_overdue_property(self):
        """正常系 → 異常系: 延滞判定ロジックの検証"""
        # 正常系: 未来の期限
        lending = LendingFactory(due_date=timezone.now().date() + timezone.timedelta(days=1))
        self.assertFalse(lending.is_overdue)

        # 境界値: 期限当日
        lending.due_date = timezone.now().date()
        self.assertFalse(lending.is_overdue)

        # 異常系: 期限切れ
        lending.due_date = timezone.now().date() - timezone.timedelta(days=1)
        self.assertTrue(lending.is_overdue)

    def test_days_overdue(self):
        """境界値: 延滞日数の計算（当日=0, 昨日=1）"""
        lending = LendingFactory(due_date=timezone.now().date() - timezone.timedelta(days=2))
        self.assertEqual(lending.days_overdue, 2)

        lending.due_date = timezone.now().date() + timezone.timedelta(days=1)
        self.assertEqual(lending.days_overdue, 0)


class ReservationManagerTest(TestCase):
    """
    ReservationManagerの純粋なロジック（create_reservation等）をテストする
    """

    def setUp(self):
        self.user = UserFactory()
        self.biblio = BiblioFactory()

    def test_create_reservation_success(self):
        """create_reservation: 正常にWAITING状態で作成されるか"""
        res = Reservation.objects.create_reservation(self.user, self.biblio)
        self.assertEqual(res.status, 1)  # WAITING
        self.assertTrue(res.is_active)

    def test_create_reservation_fail_already_borrowing(self):
        """create_reservation: 貸出中の本は予約できないか"""
        book = BookFactory(biblio=self.biblio)
        LendingFactory(user=self.user, book=book, status=1)  # LENDING

        with self.assertRaises(ValidationError):
            Reservation.objects.create_reservation(self.user, self.biblio)


class ReservationModelTest(TestCase, BaseModelTestMixin):
    """
    Reservationモデルのバリデーション（clean）をテストする
    """

    factory_class = ReservationFactory

    def run_str_test(self):
        """__str__ の独自形式（【予約】）を検証"""
        res = ReservationFactory()
        display_str = str(res)
        self.assertIn("【予約】", display_str)

    def test_required_fields(self):
        res = ReservationFactory()
        res.user = None
        with self.assertRaises(ValidationError):
            res.full_clean()

    # ② 個別テスト項目
    def test_clean_duplicate_reservation(self):
        """異常系: 同一ユーザーによる同一書誌の重複予約（WAITING）を阻止できるか"""
        user = UserFactory()
        biblio = BiblioFactory()
        # 1つ目の予約
        ReservationFactory(user=user, biblio=biblio, status=1)

        # 2つ目の予約（buildで作成してcleanを呼ぶ）
        duplicate_res = ReservationFactory.build(user=user, biblio=biblio, status=1)
        with self.assertRaisesRegex(ValidationError, "既にこの本に有効な予約が入っています"):
            duplicate_res.clean()
