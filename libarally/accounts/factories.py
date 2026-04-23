import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model


User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta :
        model = User

    email = factory.Faker("email")
    em_num = factory.Faker(lambda n: f"EM{1000 + n}")

    is_active = True
    is_staff = False

    lending_limit = 5
    lending_period_days = 14

    # パスワードを正しくセットするための処理、マネージャーのメソッドを呼び出す
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        password = kwargs.pop("password", "password123") # 後者はデフォルトパスワード
        user = manager.create_user(password=password, *args, **kwargs)
        return user

