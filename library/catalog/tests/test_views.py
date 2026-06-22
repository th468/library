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
        LendingFactory.create(user=self.user, book=self.book)

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
        self.assertIn('user_ready_book_ids', detail_res.context)

    def test_lib_status_anonymous_user(self):
        """未ログイン時でも、context に空のセットが含まれ、エラーにならないか"""
        response = self.client.get(reverse('catalog:booklist'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_favorite_ids'], set())
        self.assertEqual(response.context['user_lending_ids'], set())
        self.assertEqual(response.context['user_lent_book_ids'], set())
        self.assertEqual(response.context['user_ready_book_ids'], set())

    def test_favorite_toggle_re_enable_logic(self):
        """お気に入りの登録・解除・再登録が正常に動作するか（論理削除の考慮）"""
        from catalog.models import Favorite
        self.client.login(email="user@example.com", password="password123")
        url = reverse('catalog:favorite_toggle', kwargs={'pk': self.biblio.pk})

        # 1. 登録
        self.client.post(url)
        self.assertTrue(Favorite.objects.filter(user=self.user, biblio=self.biblio, is_active=True).exists())

        # 2. 解除 (論理削除)
        self.client.post(url)
        self.assertFalse(Favorite.objects.filter(user=self.user, biblio=self.biblio).exists())
        self.assertTrue(Favorite.all_objects.filter(user=self.user, biblio=self.biblio, is_active=False).exists())

        # 3. 再登録 (既存の inactive レコードを復帰させる必要がある)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Favorite.objects.filter(user=self.user, biblio=self.biblio, is_active=True).exists())

    def test_biblio_search_list_excludes_inactive_biblios(self):
        """論理削除された蔵書が検索一覧から除外されているか"""
        inactive_biblio = BiblioFactory(title="削除済みの本")
        inactive_biblio.is_active = False
        inactive_biblio.save()

        response = self.client.get(reverse('catalog:booklist'))
        self.assertEqual(response.status_code, 200)
        biblios = response.context['biblios']
        self.assertNotIn(inactive_biblio, biblios)

    def test_biblio_detail_view_404_for_inactive_biblio(self):
        """論理削除された蔵書の詳細画面は404エラーを返すか"""
        self.client.login(email="user@example.com", password="password123")
        inactive_biblio = BiblioFactory(title="削除済みの本")
        inactive_biblio.is_active = False
        inactive_biblio.save()

        url = reverse('catalog:bookdetail', kwargs={'pk': inactive_biblio.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_biblio_detail_view_excludes_inactive_books(self):
        """論理削除された書籍在庫が詳細画面の在庫一覧に表示されないか"""
        self.client.login(email="user@example.com", password="password123")
        inactive_book = BookFactory(biblio=self.biblio, shelf=self.shelf)
        inactive_book.is_active = False
        inactive_book.save()

        response = self.client.get(reverse('catalog:bookdetail', kwargs={'pk': self.biblio.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"No.{self.book.count}")
        self.assertNotContains(response, f"No.{inactive_book.count}")

