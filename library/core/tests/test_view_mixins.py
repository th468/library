from accounts.factories import UserFactory
from catalog.factories import FavoriteFactory
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.views.generic import TemplateView
from transactions.factories import LendingFactory, ReservationFactory

from core.views.mixins import LibStatusMixin


class DummyView(LibStatusMixin, TemplateView):
    template_name = "dummy.html"


class LibStatusMixinTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory.create()
        self.view = DummyView()

    def test_authenticated_user_with_data(self):
        """ログインユーザーがデータを持っている場合、正しいIDセットが取得できるか"""
        # データ作成
        favorite = FavoriteFactory.create(user=self.user)
        lending = LendingFactory.create(user=self.user)  # status=LENDING(1)
        reservation = ReservationFactory.create(user=self.user)  # status=WAITING(1)

        # リクエスト作成とユーザー割り当て
        request = self.factory.get("/")
        request.user = self.user
        self.view.request = request

        # 実行
        context = self.view.get_context_data()

        # 検証
        self.assertIn(favorite.biblio_id, context["user_favorite_ids"])
        self.assertIn(lending.book.biblio_id, context["user_lending_ids"])
        self.assertIn(reservation.biblio_id, context["user_reservation_ids"])

        # 型の検証 (set であること)
        self.assertIsInstance(context["user_favorite_ids"], set)
        self.assertIsInstance(context["user_lending_ids"], set)
        self.assertIsInstance(context["user_reservation_ids"], set)

    def test_authenticated_user_without_data(self):
        """ログインユーザーがデータを持っていない場合、空のセットが返るか"""
        request = self.factory.get("/")
        request.user = self.user
        self.view.request = request

        context = self.view.get_context_data()

        self.assertEqual(len(context["user_favorite_ids"]), 0)
        self.assertEqual(len(context["user_lending_ids"]), 0)
        self.assertEqual(len(context["user_reservation_ids"]), 0)

    def test_anonymous_user(self):
        """未ログインユーザーの場合、空のセットが返り、エラーにならないか"""
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.view.request = request

        context = self.view.get_context_data()

        self.assertEqual(context["user_favorite_ids"], set())
        self.assertEqual(context["user_lending_ids"], set())
        self.assertEqual(context["user_reservation_ids"], set())
