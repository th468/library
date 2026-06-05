from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.factories import BiblioFactory, BookFactory, FloorFactory, ShelfFactory

User = get_user_model()

class BookViewsTest(TestCase):
    """
    リファクタリング後の書籍関連ビューのテスト
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            em_num="U001",
            password="password123"
        )
        self.floor = FloorFactory()
        self.shelf = ShelfFactory(floor=self.floor)
        self.biblio = BiblioFactory(title="テスト本")
        self.book = BookFactory(biblio=self.biblio, shelf=self.shelf)

    def test_biblio_search_list_view_status(self):
        """蔵書検索一覧が正常に表示されるか"""
        response = self.client.get(reverse('catalog:booklist'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/book_list.html')
        self.assertIn('biblios', response.context)

    def test_biblio_detail_view_login_required(self):
        """詳細画面はログイン必須であるか"""
        url = reverse('catalog:bookdetail', kwargs={'pk': self.biblio.pk})
        response = self.client.get(url)
        # 未ログイン時はログイン画面へリダイレクト
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_biblio_detail_view_success(self):
        """ログイン時に詳細画面が正常に表示され、関連データが含まれているか"""
        self.client.login(email="user@example.com", password="password123")
        response = self.client.get(reverse('catalog:bookdetail', kwargs={'pk': self.biblio.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['biblio'], self.biblio)
        # 在庫(Book)が含まれているか検証
        self.assertContains(response, f"No.{self.book.count}")

    def test_biblio_search_query(self):
        """キーワード検索が正しく機能するか"""
        BiblioFactory(title="Python入門")
        BiblioFactory(title="Djangoガイド")

        # 'Python' で検索
        response = self.client.get(reverse('catalog:booklist'), {'q': 'Python'})
        self.assertEqual(len(response.context['biblios']), 1)
        self.assertEqual(response.context['biblios'][0].title, "Python入門")

    def test_lib_status_context_provided(self):
        """ログイン時、一覧および詳細ビューにユーザー状態（お気に入り等）が注入されているか"""
        from transactions.factories import LendingFactory

        from catalog.factories import FavoriteFactory

        FavoriteFactory.create(user=self.user, biblio=self.biblio)
        lending = LendingFactory.create(user=self.user, book=self.book)

        self.client.login(email="user@example.com", password="password123")

        # 1. 一覧ビューの検証
        list_res = self.client.get(reverse('catalog:booklist'))
        self.assertIn('user_favorite_ids', list_res.context)
        self.assertIn(self.biblio.id, list_res.context['user_favorite_ids'])
        self.assertIn(self.biblio.id, list_res.context['user_lending_ids'])

        # 2. 詳細ビューの検証
        detail_res = self.client.get(reverse('catalog:bookdetail', kwargs={'pk': self.biblio.pk}))
        self.assertIn('user_favorite_ids', detail_res.context)
        self.assertIn('user_lent_book_ids', detail_res.context)
        self.assertIn(self.book.id, detail_res.context['user_lent_book_ids'])

    def test_lib_status_anonymous_user(self):
        """未ログイン時でも、context に空のセットが含まれ、エラーにならないか"""
        response = self.client.get(reverse('catalog:booklist'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_favorite_ids'], set())
        self.assertEqual(response.context['user_lending_ids'], set())
        self.assertEqual(response.context['user_lent_book_ids'], set())
