from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from books.models import Book
from .models import Lending

User = get_user_model()

class LendingSystemTest(TestCase):
    def setUp(self):
        # テストデータの準備
        self.user = User.objects.create_user(username="testuser", password="password")
        # Userモデルに lending_limit や lending_period_days がある想定
        self.user.lending_limit = 5
        self.user.lending_period_days = 14
        self.user.save()

        self.staff = User.objects.create_user(username="staff", password="password", is_staff=True)
        
        self.book = Book.objects.create(title="テスト本", status=1) # 1: AVAILABLE

    def test_lend_success(self):
        """正常な貸出処理のテスト"""
        lending = Lending.objects.lend(self.user, self.book)
        
        # 本のステータスが「貸出中」になっているか
        self.book.refresh_from_db()
        self.assertEqual(self.book.status, 2) # 2: LENT
        # 返却期限が正しく計算されているか
        expected_due_date = timezone.now().date() + timedelta(days=14)
        self.assertEqual(lending.due_date, expected_due_date)

    def test_lend_failure_by_limit(self):
        """貸出上限エラーのテスト"""
        self.user.lending_limit = 0 # 上限を0に設定
        self.user.save()
        
        with self.assertRaises(ValidationError):
            Lending.objects.lend(self.user, self.book)

    def test_collect_success(self):
        """正常な返却処理のテスト"""
        lending = Lending.objects.lend(self.user, self.book)
        
        # 本人による返却
        Lending.objects.collect(lending, self.user)
        
        lending.refresh_from_db()
        self.book.refresh_from_db()
        self.assertEqual(lending.status, 2) # RETURNED
        self.assertEqual(self.book.status, 1) # AVAILABLE
        self.assertIsNotNone(lending.return_date)

    def test_collect_denied_for_other_user(self):
        """他人による返却が拒否されるか"""
        other_user = User.objects.create_user(username="other", password="password")
        lending = Lending.objects.lend(self.user, self.book)
        
        with self.assertRaises(ValidationError):
            Lending.objects.collect(lending, other_user)

    def test_renew_success(self):
        """期限延長のテスト"""
        lending = Lending.objects.lend(self.user, self.book)
        initial_due_date = lending.due_date
        
        Lending.objects.renew(lending, days=7)
        
        lending.refresh_from_db()
        self.assertEqual(lending.due_date, initial_due_date + timedelta(days=7))