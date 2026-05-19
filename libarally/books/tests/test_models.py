from core.tests.test_mixins import BaseCoreModelTest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from ..factories import BiblioFactory, BookFactory, FloorFactory, ShelfFactory
from ..models import Biblio, Book, Floor, Shelf


class BiblioModelTest(TestCase, BaseCoreModelTest):
    """
    Biblioモデルの定義と振る舞いをテストする
    """
    # ① 共通テスト項目
    def test_create_success(self):
        """Factoryでエラーなくインスタンスが作成・保存できるか"""
        biblio = BiblioFactory()
        self.assertIsInstance(biblio, Biblio)
        self.assertTrue(Biblio.objects.filter(isbn=biblio.isbn).exists())

    def test_str_representation(self):
        """__str__ が期待通りの値を返すか"""
        biblio = BiblioFactory(title="テスト駆動開発")
        self.assertEqual(str(biblio), "テスト駆動開発")

    def test_required_fields(self):
        """各必須項目を空にして full_clean() を呼んだ際、ValidationError が出るか"""
        biblio = BiblioFactory()
        biblio.title = ""
        with self.assertRaises(ValidationError) as cm:
            biblio.full_clean()
        self.assertIn('title', cm.exception.message_dict)

    def test_unique_constraint(self):
        """isbn（主キー）が重複した際、ValidationErrorが出るか"""
        BiblioFactory(isbn="978-4-00000001")
        duplicate_biblio = BiblioFactory.build(isbn="978-4-00000001")
        with self.assertRaises(ValidationError):
            # DjangoのModel.full_clean()はPK重複を検知する
            duplicate_biblio.full_clean()

    def test_max_length_constraint(self):
        """max_length を超える文字列を代入し full_clean() でエラーが出るか"""
        biblio = BiblioFactory()
        biblio.isbn = "a" * 256
        biblio.title = "a" * 256
        with self.assertRaises(ValidationError) as cm:
            biblio.full_clean()
        self.assertIn('isbn', cm.exception.message_dict)
        self.assertIn('title', cm.exception.message_dict)


class BookModelTest(TestCase):
    """
    Bookモデルの定義と振る舞いをテストする
    """
    # ① 共通テスト項目
    def test_create_success(self):
        """Factoryでエラーなくインスタンスが作成・保存できるか"""
        book = BookFactory()
        self.assertIsInstance(book, Book)
        self.assertTrue(Book.objects.filter(pk=book.pk).exists())

    def test_str_representation(self):
        """__str__ が期待通りの値を返すか"""
        biblio = BiblioFactory(title="Python入門")
        book = BookFactory(biblio=biblio) # countは1になる想定
        self.assertEqual(str(book), "Python入門,No.1")

    def test_required_fields(self):
        """各必須項目を空にして full_clean() を呼んだ際、ValidationError が出るか"""
        book = BookFactory()
        book.biblio = None
        book.shelf = None
        with self.assertRaises(ValidationError) as cm:
            book.full_clean()
        self.assertIn('biblio', cm.exception.message_dict)
        self.assertIn('shelf', cm.exception.message_dict)

    def test_unique_constraint(self):
        """UniqueConstraint (biblio, count) の重複を検証"""
        biblio = BiblioFactory()
        book1 = BookFactory(biblio=biblio)

        # 2冊目を普通に作成（これで正常な shelf も保存される）
        book2 = BookFactory(biblio=biblio)

        # 手動で book1 と同じ count をセットして保存を試みる
        book2.count = book1.count
        with self.assertRaises(IntegrityError):
            book2.save()

    def test_max_length_constraint(self):
        """Bookモデルには現状CharFieldの制限がないためパス"""
        pass

    # ② 個別テスト項目
    def test_can_be_lent_logic(self):
        """正常系 → 異常系: statusに応じたcan_be_lentの挙動テスト"""
        # 正常系: 在庫あり
        book_available = BookFactory(status=Book.Status.AVAILABLE)
        self.assertTrue(book_available.can_be_lent)

        # 異常系: 貸出中
        book_lent = BookFactory(status=Book.Status.LENT)
        self.assertFalse(book_lent.can_be_lent)

        # 異常系: メンテナンス中
        book_maint = BookFactory(status=Book.Status.MAINTENANCE)
        self.assertFalse(book_maint.can_be_lent)

    def test_save_auto_increment_count(self):
        """saveメソッドによるcountの自動採番テスト: 境界値(初回)・連続追加"""
        biblio = BiblioFactory()

        # 境界値: 最初の1冊目
        book1 = BookFactory(biblio=biblio)
        self.assertEqual(book1.count, 1)

        # 2冊目
        book2 = BookFactory(biblio=biblio)
        self.assertEqual(book2.count, 2)

        # 別のBiblioは 1 から始まるか
        other_biblio = BiblioFactory()
        other_book = BookFactory(biblio=other_biblio)
        self.assertEqual(other_book.count, 1)


class FloorModelTest(TestCase):
    """
    Floorモデルのテスト
    """
    def test_create_success(self):
        floor = FloorFactory()
        self.assertTrue(Floor.objects.filter(pk=floor.pk).exists())

    def test_str_representation(self):
        floor = FloorFactory(name="地下1階")
        self.assertEqual(str(floor), "地下1階")


class ShelfModelTest(TestCase):
    """
    Shelfモデルのテスト
    """
    def test_create_success(self):
        shelf = ShelfFactory()
        self.assertTrue(Shelf.objects.filter(pk=shelf.pk).exists())

    def test_str_representation(self):
        shelf = ShelfFactory(name="A-1")
        self.assertEqual(str(shelf), "A-1")
