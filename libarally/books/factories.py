import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

#Fakerの日本語化
FakerJP = lambda provider: factory.Faker(provider, locale="ja_JP")

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta : pass

