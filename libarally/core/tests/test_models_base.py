import factory
from django.db import connection, models
from django.test import TestCase

from core.models.base import BaseModel
from core.models.mixins import RenameUniqueFieldsMixin
from core.tests.test_mixins import BaseCoreModelTestMixin

# -----------------------------------------------------------------------------
# 1. テスト用具象モデルの定義 (Dummy Models)
# -----------------------------------------------------------------------------

class PatternA_Model(BaseModel):
    """'title' フィールドを持つモデル"""
    title = models.CharField(max_length=100)
    class Meta:
        app_label = 'core'

class PatternB_Model(BaseModel):
    """'title' は持たず 'name' フィールドを持つモデル"""
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'core'

class PatternC_Model(BaseModel):
    """どちらのフィールドも持たないモデル"""
    class Meta:
        app_label = 'core'

class UniqueRename_Model(BaseModel, RenameUniqueFieldsMixin):
    """リネーム機能を持ち、複数のユニークフィールドを持つモデル"""
    code = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    delete_unique_fields = ['code', 'slug']

    class Meta:
        app_label = 'core'

# -----------------------------------------------------------------------------
# 2. テーブルの動的管理を行う基底クラス
# -----------------------------------------------------------------------------
class SchemaManagedTestCase(TestCase):
    """ダミーモデルのテーブルを動的に作成・削除するTestCase"""

    # 管理対象のモデルリスト
    dummy_models = [
        PatternA_Model,
        PatternB_Model,
        PatternC_Model,
        UniqueRename_Model,
    ]

    @classmethod
    def setUpClass(cls):
        # super().setUpClass() の前に実行し、モデルが利用可能な状態にする
        with connection.schema_editor() as schema_editor:
            for model in cls.dummy_models:
                schema_editor.create_model(model)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # 作成時と逆の順序で削除（外部参照等がある場合の安全策）
        with connection.schema_editor() as schema_editor:
            for model in reversed(cls.dummy_models):
                schema_editor.delete_model(model)

# -----------------------------------------------------------------------------
# 3. FactoryBoyによるFactory定義
# -----------------------------------------------------------------------------

class PatternAFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PatternA_Model
    title = factory.Sequence(lambda n: f"Title {n}")

class PatternBFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PatternB_Model
    name = factory.Sequence(lambda n: f"Name {n}")

class PatternCFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PatternC_Model

class UniqueRenameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UniqueRename_Model
    code = factory.Sequence(lambda n: f"CODE_{n}")
    slug = factory.Sequence(lambda n: f"slug-{n}")

# -----------------------------------------------------------------------------
# 4. テストクラスの実装
# -----------------------------------------------------------------------------

class BaseModelComprehensiveTest(SchemaManagedTestCase, BaseCoreModelTestMixin):
    """BaseModelの全機能を一括検証する"""

    def test_everything(self):
        """全てのバリエーションを網羅実行"""

        # パターン1: titleを持つモデルの標準挙動
        with self.subTest(pattern="PatternA (title)"):
            self.factory_class = PatternAFactory
            self.test_standard_behavior()

        # パターン2: nameを持つモデルの標準挙動
        with self.subTest(pattern="PatternB (name)"):
            self.factory_class = PatternBFactory
            self.test_standard_behavior()

        # パターン3: フィールドを持たないモデルの標準挙動
        with self.subTest(pattern="PatternC (empty)"):
            self.factory_class = PatternCFactory
            self.test_standard_behavior()

        # パターン4: リネームMixinの検証
        with self.subTest(pattern="UniqueRename (mixin)"):
            self.factory_class = UniqueRenameFactory
            self.unique_fields = ['code', 'slug']
            self.unique_test_data = {'code': 'U-01', 'slug': 's-01'}
            self.test_standard_behavior()



