import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from .models import Lending, Reservation


class LendingFactory(DjangoModelFactory):
    class Meta:
        model = Lending

    # 外部アプリのモデルは'アプリ名.クラス名'の文字列指定でSubFactoryを定義
    user = factory.SubFactory("accounts.factories.UserFactory")
    book = factory.SubFactory("books.factories.BookFactory")

    # 14日後の返却期限をデフォルト設定
    due_date = factory.LazyFunction(lambda: timezone.now().date() + timezone.timedelta(days=14))
    status = Lending.Status.LENDING
    remarks = factory.Faker("word", locale="ja_JP")


class ReservationFactory(DjangoModelFactory):
    class Meta:
        model = Reservation

    user = factory.SubFactory("accounts.factories.UserFactory")
    biblio = factory.SubFactory("books.factories.BiblioFactory")
    book = None  # 初期状態（WAITING）では空
    status = Reservation.Status.WAITING
    is_active = True
