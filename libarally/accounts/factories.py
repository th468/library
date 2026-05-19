import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from .models import Department

User = get_user_model()

class DepartmentFactory(DjangoModelFactory):
    class Meta:
        model = Department

    name = factory.Faker("company", locale="ja_JP")


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    # unique=True の項目には Sequence を使用
    em_num = factory.Sequence(lambda n: f"EM{1000 + n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")

    # 日本語設定
    name = factory.Faker("name", locale="ja_JP")

    is_active = True
    is_staff = False
    lending_limit = 5
    lending_period_days = 14

    # ForeignKey の紐付け
    department = factory.SubFactory(DepartmentFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        パスワードをハッシュ化するため、マネージャーの create_user を経由させる
        """
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)
