from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from catalog.factories import BiblioFactory, BookFactory
from transactions.factories import LendingFactory, ReservationFactory
from transactions.models import Lending, Reservation

User = get_user_model()


class TransactionViewsTest(TestCase):
    """
    貸出・予約・返却・延長等のアクションビューのテスト
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            em_num="U001",
            password="password123"
        )
        self.biblio = BiblioFactory(title="テスト本")
        self.book = BookFactory(biblio=self.biblio)

    def _get_messages(self, response):
        """レスポンスからメッセージを取得するヘルパー"""
        return [m.message for m in get_messages(response.wsgi_request)]

    # --- 1. 貸出 (LendActionView) ---

    def test_lend_action_success(self):
        """正常な貸出手続き"""
        self.client.login(email="user@example.com", password="password123")
        url = reverse("transactions:lend", kwargs={"pk": self.book.pk})
        
        response = self.client.post(url)
        
        # セッションの検証（リダイレクト検証前に実行しないと、詳細画面の pop で消えてしまう）
        self.assertEqual(self.client.session.get("reveal_mode"), "lend")
        
        # Biblio詳細画面へリダイレクト
        self.assertRedirects(response, reverse("catalog:bookdetail", kwargs={"pk": self.biblio.pk}))
        
        # データベースの状態確認
        self.assertTrue(Lending.objects.filter(user=self.user, book=self.book).exists())
        
        # メッセージの確認
        messages = self._get_messages(response)
        self.assertIn(f"「{self.biblio.title}」の貸出手続きが完了しました。", messages)

    def test_lend_action_fail_already_lent(self):
        """既に貸出中の本を借りようとした場合のエラー"""
        # 他のユーザーが既に借りている状態にする
        other_user = User.objects.create_user(email="other@example.com", em_num="O001", password="pass")
        LendingFactory(user=other_user, book=self.book)
        self.book.status = self.book.Status.LENT
        self.book.save()

        self.client.login(email="user@example.com", password="password123")
        url = reverse("transactions:lend", kwargs={"pk": self.book.pk})
        
        response = self.client.post(url)
        
        # メッセージにエラーが含まれているか
        messages = self._get_messages(response)
        # e.messages をループで回すようにしたため、リストの中に直接メッセージが含まれるはず
        self.assertTrue(any("この本は現在ご利用いただけません。" in m for m in messages))

    def test_lend_action_fail_limit_reached(self):
        """貸出上限に達している場合のエラー"""
        self.user.lending_limit = 1
        self.user.save()
        
        # 既に1冊借りている状態にする
        other_book = BookFactory()
        LendingFactory(user=self.user, book=other_book)

        self.client.login(email="user@example.com", password="password123")
        url = reverse("transactions:lend", kwargs={"pk": self.book.pk})
        
        response = self.client.post(url)
        
        messages = self._get_messages(response)
        self.assertTrue(any(f"貸出上限[{self.user.lending_limit}]件に達しています。" in m for m in messages))

    def test_lend_action_fail_has_overdue(self):
        """延滞中の本がある場合のエラー"""
        from datetime import timedelta
        from django.utils import timezone
        
        # 延滞中の貸出を作る
        overdue_book = BookFactory()
        LendingFactory(
            user=self.user, 
            book=overdue_book, 
            due_date=timezone.now().date() - timedelta(days=1)
        )

        self.client.login(email="user@example.com", password="password123")
        url = reverse("transactions:lend", kwargs={"pk": self.book.pk})
        
        response = self.client.post(url)
        
        messages = self._get_messages(response)
        self.assertTrue(any("延滞中の書籍があるため、貸出できません。" in m for m in messages))

    # --- 2. 予約 (ReserveActionView) ---

    def test_reserve_action_success(self):
        """正常な予約手続き"""
        self.client.login(email="user@example.com", password="password123")
        url = reverse("transactions:reserve", kwargs={"pk": self.book.pk})
        
        response = self.client.post(url)
        
        # セッションの検証（詳細画面の pop 前に実行）
        self.assertEqual(self.client.session.get("reveal_mode"), "reserve")
        
        self.assertRedirects(response, reverse("catalog:bookdetail", kwargs={"pk": self.biblio.pk}))
        self.assertTrue(Reservation.objects.filter(user=self.user, biblio=self.biblio).exists())
        
        # メッセージの確認
        messages = self._get_messages(response)
        self.assertIn(f"「{self.biblio.title}」を予約しました。", messages)

    # --- 3. 返却 (CollectActionView) ---

    def test_collect_action_success(self):
        """正常な返却手続き"""
        lending = LendingFactory(user=self.user, book=self.book)
        self.book.status = self.book.Status.LENT
        self.book.save()

        self.client.login(email="user@example.com", password="password123")
        url = reverse("transactions:collect", kwargs={"pk": self.book.pk})
        
        response = self.client.post(url)
        
        self.assertRedirects(response, reverse("dashboard:index"))
        
        lending.refresh_from_db()
        self.assertEqual(lending.status, Lending.Status.RETURNED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.status, self.book.Status.AVAILABLE)
        
        messages = self._get_messages(response)
        self.assertIn("返却が完了しました。", messages)

    # --- 4. 延長 (RenewActionView) ---

    def test_renew_action_success(self):
        """正常な貸出延長"""
        from datetime import timedelta
        from django.utils import timezone
        # 期限を明日に設定（延滞しておらず、かつ延長によって期限が延びる状態）
        tomorrow = timezone.now().date() + timedelta(days=1)
        lending = LendingFactory(user=self.user, book=self.book, due_date=tomorrow)
        old_due_date = lending.due_date

        self.client.login(email="user@example.com", password="password123")

        url = reverse("transactions:renew", kwargs={"pk": self.book.pk})
        
        response = self.client.post(url)
        
        self.assertRedirects(response, reverse("dashboard:index"))
        
        lending.refresh_from_db()
        self.assertGreater(lending.due_date, old_due_date)
        
        messages = self._get_messages(response)
        self.assertIn("貸出期間を延長しました。", messages)

    # --- 5. 予約キャンセル (ReservationCancelActionView) ---

    def test_reservation_cancel_action_success(self):
        """正常な予約キャンセル"""
        reservation = ReservationFactory(user=self.user, biblio=self.biblio)

        self.client.login(email="user@example.com", password="password123")
        url = reverse("transactions:reserve_cancel", kwargs={"pk": reservation.pk})
        
        response = self.client.post(url)
        
        self.assertRedirects(response, reverse("dashboard:index"))
        
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CANCELED)
        
        messages = self._get_messages(response)
        self.assertIn(f"「{self.biblio.title}」の予約を取り消しました。", messages)
