from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from books.factories import BiblioFactory, BookFactory, ShelfFactory, FloorFactory

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
        response = self.client.get(reverse('books:booklist'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'books/book_list.html')
        self.assertIn('biblios', response.context)

    def test_biblio_detail_view_login_required(self):
        """詳細画面はログイン必須であるか"""
        url = reverse('books:bookdetail', kwargs={'pk': self.biblio.pk})
        response = self.client.get(url)
        # 未ログイン時はログイン画面へリダイレクト
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_biblio_detail_view_success(self):
        """ログイン時に詳細画面が正常に表示され、関連データが含まれているか"""
        self.client.login(email="user@example.com", password="password123")
        response = self.client.get(reverse('books:bookdetail', kwargs={'pk': self.biblio.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['biblio'], self.biblio)
        # 在庫(Book)が含まれているか検証
        self.assertContains(response, f"No.{self.book.count}")

    def test_biblio_search_query(self):
        """キーワード検索が正しく機能するか"""
        BiblioFactory(title="Python入門")
        BiblioFactory(title="Djangoガイド")
        
        # 'Python' で検索
        response = self.client.get(reverse('books:booklist'), {'q': 'Python'})
        self.assertEqual(len(response.context['biblios']), 1)
        self.assertEqual(response.context['biblios'][0].title, "Python入門")
