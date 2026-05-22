from core.tests.test_mixins import BaseModelTestMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from ..factories import BiblioFactory, BookFactory, FloorFactory, ShelfFactory
from ..models import Book


class BiblioModelTest(TestCase, BaseModelTestMixin):
    """
    Biblioモデルの定義と振る舞いをテストする
    """

    factory_class = BiblioFactory

    def run_str_test(self):
        """__str__ の独自形式（【書誌】）を検証"""
        biblio = BiblioFactory(title="テスト本")
        display_str = str(biblio)
        self.assertIn("【書誌】", display_str)
        self.assertIn("テスト本", display_str)

    def test_required_fields(self):
        """各必須項目を空にして full_clean() を呼んだ際、ValidationError が出るか"""
        biblio = BiblioFactory()
        biblio.title = ""
        with self.assertRaises(ValidationError) as cm:
            biblio.full_clean()
        self.assertIn("title", cm.exception.message_dict)

    def test_unique_constraint(self):
        """isbn（ユニークフィールド）が重複した際、ValidationErrorが出るか"""
        BiblioFactory(isbn="978-4-00000001")
        duplicate_biblio = BiblioFactory.build(isbn="978-4-00000001")
        with self.assertRaises(ValidationError):
            duplicate_biblio.full_clean()

    def test_max_length_constraint(self):
        """max_length を超える文字列を代入し full_clean() でエラーが出るか"""
        biblio = BiblioFactory()
        biblio.isbn = "a" * 256
        biblio.title = "a" * 256
        with self.assertRaises(ValidationError) as cm:
            biblio.full_clean()
        self.assertIn("isbn", cm.exception.message_dict)
        self.assertIn("title", cm.exception.message_dict)


class BookModelTest(TestCase, BaseModelTestMixin):
    """
    Bookモデルの定義と振る舞いをテストする
    """

    factory_class = BookFactory

    def run_str_test(self):
        """__str__ の独自形式（【現物】）を検証"""
        biblio = BiblioFactory(title="Python入門")
        book = BookFactory(biblio=biblio)
        display_str = str(book)
        self.assertIn("【現物】", display_str)
        self.assertIn("Python入門", display_str)
        self.assertIn("No.1", display_str)

    def test_required_fields(self):
        """各必須項目を空にして full_clean() を呼んだ際、ValidationError が出るか"""
        book = BookFactory()
        book.biblio = None
        book.shelf = None
        with self.assertRaises(ValidationError) as cm:
            book.full_clean()
        self.assertIn("biblio", cm.exception.message_dict)
        self.assertIn("shelf", cm.exception.message_dict)

    def test_unique_constraint(self):
        """UniqueConstraint (biblio, count) の重複を検証"""
        biblio = BiblioFactory()
        book1 = BookFactory(biblio=biblio)

        # 2冊目を普通に作成
        book2 = BookFactory(biblio=biblio)

        # 手動で book1 と同じ count をセットして保存を試みる
        book2.count = book1.count
        with self.assertRaises(IntegrityError):
            book2.save()

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
        """saveメソッドによるcountの自動採番テスト"""
        biblio = BiblioFactory()
        book1 = BookFactory(biblio=biblio)
        self.assertEqual(book1.count, 1)

        book2 = BookFactory(biblio=biblio)
        self.assertEqual(book2.count, 2)

        other_biblio = BiblioFactory()
        other_book = BookFactory(biblio=other_biblio)
        self.assertEqual(other_book.count, 1)


class FloorModelTest(TestCase, BaseModelTestMixin):
    """
    Floorモデルのテスト（BaseModelの標準検証を使用）
    """

    factory_class = FloorFactory


class ShelfModelTest(TestCase, BaseModelTestMixin):
    """
    Shelfモデルのテスト（BaseModelの標準検証を使用）
    """

    factory_class = ShelfFactory

    def test_required_fields(self):
        """必須項目（floor）のチェック"""
        shelf = ShelfFactory()
        shelf.floor = None
        with self.assertRaises(ValidationError):
            shelf.full_clean()
