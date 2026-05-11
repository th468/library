import factory
from django.db import connection, models
from django.test import TestCase

# 基盤クラスとMixinのインポート
from core.models.base import BaseModel
from core.models.mixins import RenameUniqueFieldsMixin
from core.tests.test_mixins import BaseModelBehaviorMixin, RenameUniqueTestMixin

# ----------------------------------------------------------------      
# 1. テスト用ダミーモデルの定義
# ----------------------------------------------------------------

class TestModel(BaseModel):
    """BaseModelの基本機能を検証するためのダミーモデル"""
    class Meta:
        app_label = 'core'  # schema_editor実行のために必要


class TestUniqueModel(BaseModel, RenameUniqueFieldsMixin):
    """リネーム機能を検証するためのユニーク制約を持つダミーモデル"""
    code = models.CharField(max_length=10, unique=True)
    
    delete_unique_fields = ['code']

    class Meta:
        app_label = 'core'


# ----------------------------------------------------------------      
# 2. Factoryの定義
# ----------------------------------------------------------------

class TestModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TestModel
    
    remarks = factory.Faker('sentence')


class TestUniqueModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TestUniqueModel
    
    code = factory.Sequence(lambda n: f'CODE{n:03}')
    remarks = factory.Faker('sentence')


# ----------------------------------------------------------------      
# 3. テストクラスの実装
# ----------------------------------------------------------------

class BaseSchemaTestCase(TestCase):
    """ダミーモデル用のテーブルを動的に作成・削除する基底クラス"""
    
    @classmethod
    def setUpClass(cls):
        # 参照されているダミーモデルのリスト
        cls.test_models = [TestModel, TestUniqueModel]
        
        # 実際にDBにテーブルを作成する
        with connection.schema_editor() as schema_editor:
            for model in cls.test_models:
                schema_editor.create_model(model)
        
        # 最後に標準のsetUpClassを呼び出す
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        # 標準のtearDownClassを先に呼び出す
        super().tearDownClass()
        
        # 作成したテーブルを削除（作成時と逆の順序）
        with connection.schema_editor() as schema_editor:
            for model in reversed(cls.test_models):
                schema_editor.delete_model(model)


class TestModelTest(BaseSchemaTestCase, BaseModelBehaviorMixin):
    """BaseModel の基本挙動テスト"""

    def test_base_behavior(self):
        """BaseModelの共通機能を一括検証する"""
        factory_class = TestModelFactory
        
        # 1. objects(有効データのみ) と all_objects(削除済含む全データ) が正しく分離されているか検証
        self.assert_managers_strictly_separated(factory_class)

        # 2. インスタンスの delete() 実行時に、論理削除フラグが立ち、更新日時が正しく変わるか検証
        self.assert_logical_delete_instance(factory_class)

        # 3. クエリセットの delete()（バルク削除）で、複数レコードが一括で論理削除されるか検証
        self.assert_logical_delete_queryset(factory_class)

        # 4. hard_delete() を呼んだ際に、論理削除ではなくDBから物理的にデータが消えるか検証
        self.assert_hard_delete_behavior(factory_class)

        # 5. 作成日時(created_at)の自動付与や __str__ の表示形式が仕様通りか検証
        self.assert_base_model_logic(factory_class)


class TestUniqueModelTest(BaseSchemaTestCase, BaseModelBehaviorMixin, RenameUniqueTestMixin):
    """TestUniqueModel (BaseModel + RenameUniqueFieldsMixin) の挙動テスト"""

    def test_base_behavior(self):
        """リネーム対象モデルでも基本機能（論理削除等）が壊れていないか検証"""
        self.assert_managers_strictly_separated(TestUniqueModelFactory)
        self.assert_logical_delete_instance(TestUniqueModelFactory)
        self.assert_logical_delete_queryset(TestUniqueModelFactory)
        self.assert_hard_delete_behavior(TestUniqueModelFactory)
        self.assert_base_model_logic(TestUniqueModelFactory)

    def test_rename_behavior(self):
        """リネーム機能に特化した検証"""
        factory_class = TestUniqueModelFactory
        
        # 1. サフィックス付与の検証
        self.assert_rename_works(factory_class, unique_fields=['code'])
        
        # 2. 二重リネーム防止の検証
        self.assert_double_rename_protection(factory_class)
        
        # 3. 削除後の同一値での再登録検証
        self.assert_unique_constraint_cleared(factory_class, unique_data={'code': 'UNIQUE01'})
        
        # 4. 存在しないフィールド指定時の堅牢性検証
        self.assert_rename_robustness(factory_class)