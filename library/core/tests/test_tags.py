from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from core.templatetags.core_tags import render_breadcrumbs
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
