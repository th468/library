from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from core.templatetags.core_tags import render_breadcrumbs, is_lent_by, is_reserved_by
from catalog.factories import BiblioFactory, BookFactory, ShelfFactory, FloorFactory
from transactions.models import Lending, Reservation

User = get_user_model()

class CoreTagsTest(TestCase):
    """
    カスタムテンプレートタグ（フィルタ）のテスト
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com", 
            em_num="TEST001", 
            password="password123"
        )

    def test_render_breadcrumbs_logic(self):
        """URLパスから日本語ラベル付きのパンくずが正しく生成されるか"""
        # 1. 検索一覧パス
        request = self.factory.get('/catalog/list/')
        context = {'request': request}
        result = render_breadcrumbs(context)
        self.assertEqual(result['links'][0]['label'], '蔵書をさがす')
        self.assertEqual(result['links'][1]['label'], '検索結果')

        # 2. 詳細パス（数値IDを含む）
        request = self.factory.get('/catalog/detail/1/')
        context = {'request': request}
        result = render_breadcrumbs(context)
        self.assertEqual(result['links'][1]['label'], '書籍詳細')
        self.assertEqual(result['links'][2]['label'], '詳細')

        # 3. ダッシュボード
        request = self.factory.get('/dashboard/')
        context = {'request': request}
        result = render_breadcrumbs(context)
        self.assertEqual(result['links'][0]['label'], 'マイページ')

    def test_is_lent_by_filter(self):
        """is_lent_by フィルタが貸出状況を正しく判定するか（Biblio/Book両対応）"""
        biblio = BiblioFactory()
        floor = FloorFactory()
        shelf = ShelfFactory(floor=floor)
        book = BookFactory(biblio=biblio, shelf=shelf)
        
        # 初期状態（借りていない）
        self.assertFalse(is_lent_by(biblio, self.user))
        self.assertFalse(is_lent_by(book, self.user))

        # 貸出実行
        Lending.objects.lend(book, self.user)
        
        # 貸出中状態の判定
        self.assertTrue(is_lent_by(biblio, self.user)) # 書誌単位での判定
        self.assertTrue(is_lent_by(book, self.user))   # 個体単位での判定

    def test_is_reserved_by_filter(self):
        """is_reserved_by フィルタが予約状況を正しく判定するか"""
        biblio = BiblioFactory()
        
        # 初期状態（予約していない）
        self.assertFalse(is_reserved_by(biblio, self.user))

        # 予約実行
        Reservation.objects.create_reservation(self.user, biblio)
        
        # 予約中状態の判定
        self.assertTrue(is_reserved_by(biblio, self.user))
