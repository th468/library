from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.factories import UserFactory
from catalog.factories import BiblioFactory, BookFactory
from transactions.factories import LendingFactory
from transactions.models import Lending

class DashboardIndexViewTest(TestCase):
    """
    DashboardIndexView のテスト
    """
    def test_index_view_anonymous(self):
        """未ログイン時は landing.html を使用する"""
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/landing.html")
        self.assertNotContains(response, "ダッシュボード")

    def test_index_view_authenticated(self):
        """ログイン時は index.html を使用する"""
        user = UserFactory(password="password123")
        self.client.login(email=user.email, password="password123")
        
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")
        self.assertIn("recent_biblios", response.context)
        self.assertIn("favorite_biblios", response.context)


class LendingHistoryViewTest(TestCase):
    """
    LendingHistoryView のテスト
    """
    def setUp(self):
        self.user = UserFactory(password="password123")
        self.other_user = UserFactory()
        
        # 自分の返却済み履歴
        self.biblio1 = BiblioFactory(title="マイブック")
        self.book1 = BookFactory(biblio=self.biblio1)
        self.lending1 = LendingFactory(
            user=self.user, 
            book=self.book1, 
            status=Lending.Status.RETURNED,
            return_date=timezone.now().date()
        )
        
        # 自分の貸出中（履歴には出ないはず）
        self.biblio2 = BiblioFactory(title="貸出中の本")
        self.book2 = BookFactory(biblio=self.biblio2)
        self.lending2 = LendingFactory(user=self.user, book=self.book2, status=Lending.Status.LENDING)
        
        # 他人の返却済み履歴（履歴には出ないはず）
        self.biblio3 = BiblioFactory(title="他人の本")
        self.book3 = BookFactory(biblio=self.biblio3)
        self.lending3 = LendingFactory(
            user=self.other_user, 
            book=self.book3, 
            status=Lending.Status.RETURNED,
            return_date=timezone.now().date()
        )

    def test_lending_history_login_required(self):
        """未ログイン時はログイン画面にリダイレクトされる"""
        response = self.client.get(reverse("dashboard:history"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard:history')}")

    def test_lending_history_queryset(self):
        """ログインユーザー自身の返却済み履歴のみが表示される"""
        self.client.login(email=self.user.email, password="password123")
        response = self.client.get(reverse("dashboard:history"))
        
        self.assertEqual(response.status_code, 200)
        history_list = response.context["history_list"]
        
        # 1件（lending1）のみ含まれることを確認
        self.assertEqual(len(history_list), 1)
        self.assertIn(self.lending1, history_list)
        self.assertNotIn(self.lending2, history_list)
        self.assertNotIn(self.lending3, history_list)
        
        # テンプレートに表示されているか
        self.assertContains(response, "マイブック")
        self.assertNotContains(response, "貸出中の本")
        self.assertNotContains(response, "他人の本")
