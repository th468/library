from accounts.factories import UserFactory
from catalog.factories import BiblioFactory, BookFactory, CategoryFactory
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.http import urlencode
from transactions.factories import LendingFactory

from core.templatetags.core_tags import (
    active_link,
    get_category_list,
    get_item,
    global_search_bar,
    is_lent_by_others,
    relative_url,
    render_breadcrumbs,
    user_lending,
)


class CoreTagsTestCase(TestCase):
    """
    core_tags.py に定義された全てのカスタムタグおよびフィルタのテスト
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory()

    # --- UI Component Tests ---

    def test_get_category_list(self):
        """カテゴリリストが名前順で取得されるか"""
        c1 = CategoryFactory(name="B")
        c2 = CategoryFactory(name="A")
        c3 = CategoryFactory(name="C")

        result = get_category_list()
        categories = list(result["categories"])

        self.assertEqual(len(categories), 3)
        self.assertEqual(categories[0], c2)  # A
        self.assertEqual(categories[1], c1)  # B
        self.assertEqual(categories[2], c3)  # C

    def test_global_search_bar(self):
        """検索バーに現在のクエリパラメータが反映されるか"""
        # クエリあり
        request = self.factory.get("/", {"q": "python"})
        result = global_search_bar({"request": request})
        self.assertEqual(result["q"], "python")

        # クエリなし
        request = self.factory.get("/")
        result = global_search_bar({"request": request})
        self.assertEqual(result["q"], "")

        # request なし (エッジケース)
        result = global_search_bar({})
        self.assertEqual(result["q"], "")

    # --- Navigation & URL Tests ---

    def test_active_link(self):
        """現在のパスに応じて active クラスが正しく返されるか"""
        target_url_name = "catalog:booklist"
        target_path = reverse(target_url_name)  # /catalog/book/

        # 完全一致
        request = self.factory.get(target_path)
        self.assertEqual(active_link({"request": request}, target_url_name), "active")

        # 前方一致 (詳細画面などで親メニューをハイライトする挙動)
        # ※実際のアプリ構造に合わせたパスで検証
        detail_path = f"{target_path}detail/1/"
        request = self.factory.get(detail_path)
        self.assertEqual(active_link({"request": request}, target_url_name), "active")

        # 不一致
        request = self.factory.get("/accounts/login/")
        self.assertEqual(active_link({"request": request}, target_url_name), "")

        # カスタムCSSクラス
        request = self.factory.get(target_path)
        self.assertEqual(
            active_link({"request": request}, target_url_name, "is-active"), "is-active"
        )

    def test_render_breadcrumbs(self):
        """URLパスから階層的なパンくずリストが生成されるか"""
        # 書籍詳細画面へのパスをシミュレート
        biblio = BiblioFactory()
        # /catalog/book/detail/<pk>/
        path = reverse("catalog:bookdetail", kwargs={"pk": biblio.pk})
        request = self.factory.get(path)

        result = render_breadcrumbs({"request": request})
        links = result["links"]

        # 1. 蔵書一覧 (/catalog/book/)
        # 2. 書籍詳細 (/catalog/book/detail/<pk>/)
        self.assertEqual(len(links), 2)

        self.assertEqual(links[0]["label"], "蔵書をさがす")
        self.assertEqual(links[0]["url"], "/catalog/book/")

        self.assertEqual(links[1]["label"], "書籍詳細")
        self.assertEqual(links[1]["url"], path)

    def test_render_breadcrumbs_root(self):
        """ルートパスではパンくずが表示されないか"""
        request = self.factory.get("/")
        result = render_breadcrumbs({"request": request})
        self.assertEqual(len(result["links"]), 0)

    def test_relative_url(self):
        """URLパラメータが正しく維持・置換されるか"""
        # 新規パラメータの追加
        result = relative_url(2, "page")
        self.assertEqual(result, "?page=2")

        # 既存パラメータの維持と特定パラメータの置換
        existing_params = urlencode({"q": "python", "page": "1", "sort": "name"})
        result = relative_url(2, "page", existing_params)

        # page=2 に書き換わり、q=python と sort=name は維持される必要がある
        self.assertIn("page=2", result)
        self.assertIn("q=python", result)
        self.assertIn("sort=name", result)
        self.assertNotIn("page=1", result)

    # --- Utility Filter Tests ---

    def test_get_item(self):
        """辞書からキーで値を取得できるか"""
        data = {"key1": "value1", "key2": 100}
        self.assertEqual(get_item(data, "key1"), "value1")
        self.assertEqual(get_item(data, "key2"), 100)
        self.assertEqual(get_item(data, "invalid"), None)
        self.assertEqual(get_item(None, "key1"), None)

    # --- Business Logic Filter Tests ---

    def test_is_lent_by_others(self):
        """他ユーザーによる貸出判定の検証"""
        biblio = BiblioFactory()
        book = BookFactory(biblio=biblio)
        other_user = UserFactory()

        # ケース1: 誰も借りていない
        self.assertFalse(is_lent_by_others(biblio, self.user))

        # ケース2: 自分が借りている
        LendingFactory(book=book, user=self.user, return_date=None)
        self.assertFalse(is_lent_by_others(biblio, self.user))

        # ケース3: 他人が借りている
        # 別の在庫(Book)を作成して他人が借りる状況を作る
        book2 = BookFactory(biblio=biblio)
        LendingFactory(book=book2, user=other_user, return_date=None)
        self.assertTrue(is_lent_by_others(biblio, self.user))

        # 未ログインユーザーの場合
        self.assertFalse(is_lent_by_others(biblio, None))

    def test_user_lending(self):
        """自身が貸出中の Lending オブジェクトが取得できるか"""
        biblio = BiblioFactory()
        book = BookFactory(biblio=biblio)

        # 貸出前
        self.assertIsNone(user_lending(biblio, self.user))

        # 貸出中
        lending = LendingFactory(book=book, user=self.user, return_date=None)
        result = user_lending(biblio, self.user)
        self.assertEqual(result, lending)

        # 返却済みの場合は取得されない
        lending.return_date = lending.due_date
        lending.save()
        self.assertIsNone(user_lending(biblio, self.user))
