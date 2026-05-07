import datetime
import factory
from factory.django import DjangoModelFactory
from django.test import TestCase
from django.db import models, IntegrityError
from core.models import BaseModel

# --- 1. テスト用の具象モデル ---
# このファイル内だけで完結させる
class TestModel(BaseModel):
    code = models.CharField("コード", max_length=100, unique=True)
    title = models.CharField("タイトル", max_length=100, null=True, blank=True)
    
    delete_unique_fields = ['code']

    class Meta:
        app_label = 'core'

# --- 2. テスト用モデルのFactory ---
# 相互インポートを防ぐため、ここに定義する
class TestModelFactory(DjangoModelFactory):
    class Meta:
        model = TestModel

    code = factory.Sequence(lambda n: f"code-{n}")
    title = factory.Faker("word", locale="ja_JP")
    is_active = True

# --- 3. テストクラス群 ---

class BaseManagerAndQuerySetTest(TestCase):
    def setUp(self):
        self.objs = TestModelFactory.create_batch(3)

    def test_queryset_logical_delete(self):
        """TestModel.objects.all().delete() で is_active=False に更新されるか"""
        TestModel.objects.all().delete()
        all_data = TestModel.all_objects.all()
        self.assertEqual(all_data.count(), 3)
        for obj in all_data:
            self.assertFalse(obj.is_active)

    def test_queryset_hard_delete(self):
        """hard_delete() で物理削除されるか"""
        TestModel.objects.all().hard_delete()
        self.assertEqual(TestModel.all_objects.count(), 0)

    def test_manager_active_filter(self):
        """objects.all() がデフォルトで is_active=True のみを返すか"""
        TestModelFactory(is_active=False)
        active_count = TestModel.objects.count()
        self.assertEqual(active_count, 3)

    def test_all_objects_manager(self):
        """all_objects.all() で全件取得できるか"""
        TestModelFactory(is_active=False)
        self.assertEqual(TestModel.all_objects.count(), 4)


class BaseModelInstanceTest(TestCase):
    def test_instance_logical_delete(self):
        obj = TestModelFactory(title="削除テスト")
        obj.delete()
        obj.refresh_from_db()
        self.assertFalse(obj.is_active)

    def test_instance_hard_delete(self):
        obj = TestModelFactory()
        obj.hard_delete()
        self.assertFalse(TestModel.all_objects.filter(pk=obj.pk).exists())

    def test_unique_field_rename(self):
        original_code = "UNIQUE-001"
        obj = TestModelFactory(code=original_code)
        
        obj.delete()
        obj.refresh_from_db()
        
        self.assertIn("_del_", obj.code)

        # 同じコードで新しく作成できるか
        try:
            TestModelFactory(code=original_code)
        except IntegrityError:
            self.fail("一意制約のリネームが機能していません")

    def test_str_representation(self):
        obj = TestModelFactory(title="テスト")
        self.assertEqual(str(obj), f"[{obj.pk}] テスト")
        
        obj_no_title = TestModelFactory(title=None)
        self.assertEqual(str(obj_no_title), f"[{obj_no_title.pk}] TestModel")

    def test_updated_at_change(self):
        obj = TestModelFactory()
        old_updated_at = obj.updated_at
        obj.delete()
        obj.refresh_from_db()
        self.assertGreater(obj.updated_at, old_updated_at)