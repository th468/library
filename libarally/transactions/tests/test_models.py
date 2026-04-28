from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from accounts.factories import UserFactory
from books.factories import BookFactory, BiblioFactory
from ..models import Lending, Reservation
from ..factories import LendingFactory, ReservationFactory

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
        
        # 書籍が取り置き状態（RESERVED=3想定）になっているか
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


class LendingModelTest(TestCase):
    """
    Lendingモデルの定義とプロパティの振る舞いをテストする
    """
    # ① 共通テスト項目
    def test_create_success(self):
        lending = LendingFactory()
        self.assertTrue(Lending.objects.filter(pk=lending.pk).exists())

    def test_str_representation(self):
        # TransactionBase依存のデフォルト挙動を確認
        lending = LendingFactory()
        self.assertIn("Lending object", str(lending))

    def test_required_fields(self):
        lending = LendingFactory()
        lending.user = None
        with self.assertRaises(ValidationError):
            lending.full_clean()

    def test_unique_constraint(self):
        # Lendingには現状unique=Trueがないためパス
        pass

    def test_max_length_constraint(self):
        # statusはChoices(Integer)のため対象外
        pass

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
        LendingFactory(user=self.user, book=book, status=1) # LENDING
        
        with self.assertRaises(ValidationError):
            Reservation.objects.create_reservation(self.user, self.biblio)


class ReservationModelTest(TestCase):
    """
    Reservationモデルのバリデーション（clean）をテストする
    """
    # ① 共通テスト項目
    def test_create_success(self):
        res = ReservationFactory()
        self.assertTrue(Reservation.objects.filter(pk=res.pk).exists())

    def test_str_representation(self):
        res = ReservationFactory()
        self.assertIn("Reservation object", str(res))

    def test_required_fields(self):
        res = ReservationFactory()
        res.user = None
        with self.assertRaises(ValidationError):
            res.full_clean()

    def test_unique_constraint(self):
        pass

    def test_max_length_constraint(self):
        pass

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