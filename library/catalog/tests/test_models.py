from core.tests.test_mixins import BaseModelTestMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from ..factories import (
    BiblioFactory,
    BookFactory,
    CategoryFactory,
    FavoriteFactory,
    FloorFactory,
    ShelfFactory,
)


class CategoryModelTest(TestCase, BaseModelTestMixin):
    """
    Categoryモデルのテスト
    """

    factory_class = CategoryFactory


class BiblioModelTest(TestCase, BaseModelTestMixin):
    """
    Biblioモデルの定義とリレーションをテストする
    """

    factory_class = BiblioFactory

    def run_str_test(self):
        """__str__ の独自形式（【書誌】）を検証"""
        biblio = BiblioFactory(title="テスト本")
        self.assertIn("【書誌】", str(biblio))
        self.assertIn("テスト本", str(biblio))

    def test_category_relation(self):
        """正常系: 多対多リレーションの動作確認"""
        biblio = BiblioFactory()
        cat1 = CategoryFactory(name="技術書")
        cat2 = CategoryFactory(name="Python")

        # 1. カテゴリを2つ追加
        biblio.categories.add(cat1, cat2)

        # 2. 正しく紐付いているか確認
        self.assertEqual(biblio.categories.count(), 2)
        self.assertIn(cat1, biblio.categories.all())

        # 3. 逆方向（カテゴリ側）からも本を参照できるか確認
        self.assertIn(biblio, cat1.biblios.all())

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
        """__str__ の独自形式を検証"""
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

    def test_can_be_reserved_logic(self):
        """正常系 → 異常系: statusに応じたcan_be_reservedの挙動テスト"""
        model_class = self.factory_class._meta.model

        # 正常系: 在庫あり・貸出中・予約中は予約対象
        self.assertTrue(BookFactory(status=model_class.Status.AVAILABLE).can_be_reserved)
        self.assertTrue(BookFactory(status=model_class.Status.LENT).can_be_reserved)
        self.assertTrue(BookFactory(status=model_class.Status.RESERVED).can_be_reserved)

        # 異常系: メンテナンス中・紛失は予約対象外
        self.assertFalse(BookFactory(status=model_class.Status.MAINTENANCE).can_be_reserved)
        self.assertFalse(BookFactory(status=model_class.Status.LOST).can_be_reserved)

    def test_can_be_lent_to_logic(self):
        """statusおよび予約状況に応じたcan_be_lent_toの挙動テスト"""
        from accounts.factories import UserFactory
        from transactions.factories import ReservationFactory

        Book = self.factory_class._meta.model

        user1 = UserFactory()
        user2 = UserFactory()

        # 1. AVAILABLE（在庫あり）: 誰でも貸出可能
        book_available = BookFactory(status=Book.Status.AVAILABLE)
        self.assertTrue(book_available.can_be_lent_to(user1))
        self.assertTrue(book_available.can_be_lent_to(user2))
        self.assertTrue(book_available.can_be_lent_to(None))

        # 2. LENT（貸出中）: 誰に対しても貸出不可
        book_lent = BookFactory(status=Book.Status.LENT)
        self.assertFalse(book_lent.can_be_lent_to(user1))
        self.assertFalse(book_lent.can_be_lent_to(user2))
        self.assertFalse(book_lent.can_be_lent_to(None))

        # 3. RESERVED（予約中）:
        book_reserved = BookFactory(status=Book.Status.RESERVED)

        # 3a. 自身向けの READY (準備完了) 予約が存在する場合のみ貸出可能
        res1 = ReservationFactory(user=user1, book=book_reserved, status=2)  # READY
        self.assertTrue(book_reserved.can_be_lent_to(user1))
        # 3b. 他人向けの予約なので貸出不可
        self.assertFalse(book_reserved.can_be_lent_to(user2))
        self.assertFalse(book_reserved.can_be_lent_to(None))

        # 3c. 予約が存在しても WAITING (入荷待ち) などの状態であれば貸出不可
        res1.status = 1  # WAITING
        res1.save()
        self.assertFalse(book_reserved.can_be_lent_to(user1))

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


class FavoriteModelTest(TestCase, BaseModelTestMixin):
    """
    Favoriteモデルのテスト
    """

    factory_class = FavoriteFactory

    def run_str_test(self):
        """__str__ の独自形式（【お気に入り】）を検証"""
        favorite = FavoriteFactory()
        display_str = str(favorite)
        self.assertIn("【お気に入り】", display_str)
        self.assertIn(favorite.user.email, display_str)

    def test_unique_constraint(self):
        """同一ユーザーによる同一書誌の重複登録を阻止できるか"""
        favorite = FavoriteFactory()
        # 同じ組み合わせで作成を試みる
        duplicate = FavoriteFactory.build(user=favorite.user, biblio=favorite.biblio)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
