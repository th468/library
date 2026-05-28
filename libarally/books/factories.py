import factory
from factory.django import DjangoModelFactory

from accounts.factories import UserFactory
from .models import Biblio, Book, Category, Favorite, Floor, Shelf


class FloorFactory(DjangoModelFactory):
    class Meta:
        model = Floor

    name = factory.Sequence(lambda n: f"{n + 1}F")


class ShelfFactory(DjangoModelFactory):
    class Meta:
        model = Shelf

    name = factory.Sequence(lambda n: f"棚-{n:03d}")
    floor = factory.SubFactory(FloorFactory)


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"カテゴリ-{n:02d}")


class BiblioFactory(DjangoModelFactory):
    class Meta:
        model = Biblio

    # ISBNは主キーかつ一意である必要があるためSequenceを使用
    isbn = factory.Sequence(lambda n: f"978-4-{n:08d}")
    title = factory.Faker("word", locale="ja_JP")
    author = factory.Faker("name", locale="ja_JP")
    publisher = factory.Faker("company", locale="ja_JP")


class BookFactory(DjangoModelFactory):
    class Meta:
        model = Book

    biblio = factory.SubFactory(BiblioFactory)
    shelf = factory.SubFactory(ShelfFactory)
    status = Book.Status.AVAILABLE
    # count は save メソッドで自動採番されるため、あえて指定しない


class FavoriteFactory(DjangoModelFactory):
    class Meta:
        model = Favorite

    user = factory.SubFactory(UserFactory)
    biblio = factory.SubFactory(BiblioFactory)
