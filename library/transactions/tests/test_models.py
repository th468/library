from accounts.factories import UserFactory
from catalog.factories import BiblioFactory, BookFactory
from core.tests.test_mixins import BaseModelTestMixin
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from ..factories import LendingFactory, ReservationFactory
from ..models import Lending, Reservation


class LendingManagerTest(TestCase):
    """
    LendingManagerの純粋なロジック（lend, collect, renew）をテストする
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

    def test_lend_completes_own_reservation(self):
        """lend: 予約していた本を借りた際、予約が自動的に完了（COMPLETED）になるか"""
        # 1. 準備完了状態の予約を作成
        res = Reservation.objects.create_reservation(self.user, self.biblio)
        self.assertEqual(res.status, 2)  # READY
        self.assertEqual(res.book, self.book)

        # 2. 貸出実行
        Lending.objects.lend(self.book, self.user)

        # 3. 予約が完了しているか検証
        res.refresh_from_db()
        self.assertEqual(res.status, 3)  # COMPLETED

    def test_collect_success_no_reservation(self):
        """collect: 予約がない場合、返却後に書籍がAVAILABLEに戻るか"""
        lending = Lending.objects.lend(self.book, self.user)
        Lending.objects.collect(lending, self.user)
        self.book.refresh_from_db()
        self.assertEqual(self.book.status, 1)  # AVAILABLE

    def test_collect_and_trigger_reservation(self):
        """collect: 待機中の予約がある場合、返却後に書籍がRESERVEDになり予約がREADYになるか"""
        # 1. まず貸し出す（これで在庫がなくなる）
        lending = Lending.objects.lend(self.book, self.user)

        # 2. 他のユーザーが同じ書誌を予約（在庫がないので WAITING になる）
        other_user = UserFactory()
        reservation = Reservation.objects.create_reservation(other_user, self.biblio)
        self.assertEqual(reservation.status, 1)  # WAITING

        # 3. 返却実行（トリガー発動）
        Lending.objects.collect(lending, self.user)

        # 4. 検証
        self.book.refresh_from_db()
        # RESERVED の値は 3 であることを確認 (AVAILABLE=1, LENT=2, RESERVED=3)
        self.assertEqual(self.book.status, 3)  # RESERVED

        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 2)  # READY
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
        """__str__ の独自形式を検証"""
        lending = LendingFactory()
        display_str = str(lending)
        self.assertIn("【貸出】", display_str)

    def test_required_fields(self):
        lending = LendingFactory()
        lending.user = None
        with self.assertRaises(ValidationError):
            lending.full_clean()

    def test_is_overdue_property(self):
        lending = LendingFactory(due_date=timezone.now().date() + timezone.timedelta(days=1))
        self.assertFalse(lending.is_overdue)

        lending.due_date = timezone.now().date() - timezone.timedelta(days=1)
        self.assertTrue(lending.is_overdue)


class ReservationManagerTest(TestCase):
    """
    ReservationManagerのロジック（即時引き当て等）をテストする
    """

    def setUp(self):
        self.user = UserFactory()
        self.biblio = BiblioFactory()

    def test_create_reservation_immediate_allocation(self):
        """create_reservation: 在庫がある場合、即座にREADY状態で作成されるか"""
        book = BookFactory(biblio=self.biblio, status=1)  # AVAILABLE
        res = Reservation.objects.create_reservation(self.user, self.biblio)

        # 予約がREADY(2)になっており、本が紐付いているか
        self.assertEqual(res.status, 2)
        self.assertEqual(res.book, book)
        self.assertIsNotNone(res.reserved_until)

        # 本のステータスがRESERVED(3)に変わっているか
        book.refresh_from_db()
        self.assertEqual(book.status, 3)

    def test_create_reservation_waiting_list(self):
        """create_reservation: 在庫がない場合、WAITING状態で作成されるか"""
        # 1. まず貸し出して在庫を無くす
        other_user = UserFactory()
        book = BookFactory(biblio=self.biblio, status=1)
        Lending.objects.lend(book, other_user)

        # 2. 予約実行（在庫がないので WAITING になるはず）
        res = Reservation.objects.create_reservation(self.user, self.biblio)

        # 予約がWAITING(1)になっているか
        self.assertEqual(res.status, 1)
        self.assertIsNone(res.book)

    def test_handle_expired_reservations(self):
        """handle_expired_reservations: 期限切れの予約が正しくキャンセルされ、本が解放されるか"""
        # 1. 期限切れの準備完了予約を作成
        book = BookFactory(biblio=self.biblio, status=1)
        res = Reservation.objects.create_reservation(self.user, self.biblio)
        res.reserved_until = timezone.now().date() - timezone.timedelta(days=1)
        res.save()

        # 2. 期限切れ処理を実行
        count = Reservation.objects.handle_expired_reservations()
        self.assertEqual(count, 1)

        # 3. 検証
        res.refresh_from_db()
        self.assertEqual(res.status, 4)  # CANCELED

        book.refresh_from_db()
        self.assertEqual(book.status, 1)  # AVAILABLE (次予約者がいないため)

    def test_create_reservation_fail_already_borrowing(self):
        """create_reservation: 貸出中の本は予約できないか"""
        book = BookFactory(biblio=self.biblio)
        Lending.objects.lend(book, self.user)

        with self.assertRaises(ValidationError):
            Reservation.objects.create_reservation(self.user, self.biblio)


class ReservationModelTest(TestCase, BaseModelTestMixin):
    """
    Reservationモデルのバリデーション（clean）をテストする
    """

    factory_class = ReservationFactory

    def run_str_test(self):
        """__str__ の独自形式を検証"""
        res = ReservationFactory()
        display_str = str(res)
        self.assertIn("【予約】", display_str)

    def test_required_fields(self):
        res = ReservationFactory()
        res.user = None
        with self.assertRaises(ValidationError):
            res.full_clean()

    def test_clean_duplicate_reservation(self):
        """異常系: 同一ユーザーによる同一書誌の重複予約を阻止できるか"""
        user = UserFactory()
        biblio = BiblioFactory()
        Reservation.objects.create_reservation(user, biblio)

        with self.assertRaisesRegex(ValidationError, "既にこの本に有効な予約が入っています"):
            # create_reservation を呼ぶとバリデーションが走る
            Reservation.objects.create_reservation(user, biblio)
