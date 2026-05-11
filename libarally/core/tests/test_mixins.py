import time
from django.db import IntegrityError
from django.utils import timezone

class BaseModelBehaviorMixin:
    """
    BaseModelを継承した全てのモデルに共通する基本挙動（論理削除、物理削除、
    マネージャーの分離、基本フィールド）を検証するMixin。
    """

    def _get_meta(self, factory_class):
        model = factory_class._meta.get_model_class()
        return model, model.__name__

    def assert_managers_strictly_separated(self, factory_class):
        """objects と all_objects の厳密な分離を検証"""
        model, name = _model, _name = self._get_meta(factory_class)
        
        # 準備: 有効データと削除済データを1つずつ作成
        active_obj = factory_class.create(is_active=True)
        deleted_obj = factory_class.create(is_active=False)

        # 1. objects は有効なものしか返さないこと
        self.assertIn(active_obj, model.objects.all(), msg=f"{name}: objects に有効なデータが含まれていません。")
        self.assertNotIn(deleted_obj, model.objects.all(), msg=f"{name}: objects に削除済みデータが含まれています。")
        
        # 2. objects.filter(is_active=False) は常に空であること
        self.assertEqual(model.objects.filter(is_active=False).count(), 0, 
                         msg=f"{name}: objects から論理削除済みデータが取得できてしまいます。")

        # 3. all_objects は全件返すこと
        all_count = model.all_objects.count()
        self.assertGreaterEqual(all_count, 2, msg=f"{name}: all_objects が全件（削除済含む）を返していません。")

    def assert_logical_delete_instance(self, factory_class):
        """インスタンスの delete() による論理削除を検証"""
        obj = factory_class.create()
        _, name = self._get_meta(factory_class)
        old_updated_at = obj.updated_at

        # updated_at の変化を確認するため、微小な待機を入れる（環境により同時刻になるのを防ぐ）
        time.sleep(0.001)

        obj.delete()
        obj.refresh_from_db()

        self.assertFalse(obj.is_active, msg=f"{name}: delete() 後も is_active が False になっていません。")
        self.assertGreater(obj.updated_at, old_updated_at, msg=f"{name}: delete() 時に updated_at が更新されていません。")
        
        # objects から消えているか確認
        self.assertFalse(obj.__class__.objects.filter(pk=obj.pk).exists(), 
                         msg=f"{name}: 論理削除したインスタンスが objects に残っています。")

    def assert_logical_delete_queryset(self, factory_class):
        """QuerySet.delete() によるバルク論理削除を検証"""
        model, name = self._get_meta(factory_class)
        model.all_objects.all().hard_delete()


        factory_class.create_batch(3)
        model, name = self._get_meta(factory_class)
        
        qs = model.objects.all()
        count = qs.count()
        
        # バルク削除実行
        res = qs.delete()
        
        # 戻り値が更新件数（整数）であることを確認（Django標準はタプルだが、本実装はupdateなので整数）
        self.assertIsInstance(res, int, msg=f"{name}: QuerySet.delete() の戻り値が整数ではありません。")
        self.assertEqual(model.objects.count(), 0, msg=f"{name}: バルク削除後、objects にデータが残っています。")
        self.assertEqual(model.all_objects.filter(is_active=False).count(), count, 
                         msg=f"{name}: バルク削除されたデータが all_objects(is_active=False) に正しく反映されていません。")

    def assert_hard_delete_behavior(self, factory_class):
        """物理削除 (hard_delete) の挙動を検証"""
        model, name = self._get_meta(factory_class)
        
        # インスタンスの物理削除
        obj = factory_class.create()
        obj.hard_delete()
        self.assertFalse(model.all_objects.filter(pk=obj.pk).exists(), 
                         msg=f"{name}: インスタンスの hard_delete() 後もデータがDBに残っています。")

        # クエリセットの物理削除
        factory_class.create_batch(2)
        model.all_objects.all().hard_delete()
        self.assertEqual(model.all_objects.count(), 0, 
                         msg=f"{name}: QuerySet.hard_delete() 後もデータがDBに残っています。")

    def assert_base_model_logic(self, factory_class):
        """共通フィールドと __str__ の基本ロジックを検証"""
        model, name = self._get_meta(factory_class)
        
        # 1. created_at / remarks
        obj = factory_class.create(remarks="test_remark")
        self.assertIsNotNone(obj.created_at, msg=f"{name}: created_at が自動設定されていません。")
        self.assertEqual(obj.remarks, "test_remark", msg=f"{name}: remarks が正しく保存されていません。")

        # 2. __str__ のフォールバックロジック
        # ケースA: title がある場合
        if hasattr(obj, 'title'):
            obj.title = "Sample Title"
            self.assertEqual(str(obj), f"[{obj.pk}] Sample Title", msg=f"{name}: __str__ が title を優先していません。")
        
        # ケースB: title がなく name がある場合
        obj_name = factory_class.build(name="Sample Name")
        if hasattr(obj_name, 'name') and not hasattr(obj_name, 'title'):
            obj_name.save()
            self.assertEqual(str(obj_name), f"[{obj_name.pk}] Sample Name", msg=f"{name}: __str__ が name を表示していません。")

        # ケースC: いずれもない場合（クラス名フォールバック）
        # ダミーモデル側で title/name を持たないインスタンスを生成して検証
        pure_obj = factory_class.create()
        if not hasattr(pure_obj, 'title') and not hasattr(pure_obj, 'name'):
            self.assertEqual(str(pure_obj), f"[{pure_obj.pk}] {name}", msg=f"{name}: __str__ がクラス名フォールバックになっていません。")


class RenameUniqueTestMixin:
    """
    RenameUniqueFieldsMixinを継承したモデルの、論理削除時のリネーム機能を検証するMixin。
    """

    def _get_meta(self, factory_class):
        model = factory_class._meta.get_model_class()
        return model, model.__name__

    def assert_rename_works(self, factory_class, unique_fields):
        """指定された全フィールドにサフィックスが付与されるか検証"""
        obj = factory_class.create()
        _, name = self._get_meta(factory_class)
        
        obj.delete()
        obj.refresh_from_db()

        for field in unique_fields:
            val = str(getattr(obj, field))
            self.assertIn("_del_", val, msg=f"{name}: フィールド '{field}' に削除サフィックスが含まれていません。")

    def assert_double_rename_protection(self, factory_class):
        """perform_rename() の二重実行を防止できているか検証"""
        obj = factory_class.create()
        _, name = self._get_meta(factory_class)
        
        # mixinのメソッドを直接呼ぶ
        obj.perform_rename()
        val_after_first = str(getattr(obj, obj.delete_unique_fields[0]))
        
        obj.perform_rename()
        val_after_second = str(getattr(obj, obj.delete_unique_fields[0]))

        self.assertEqual(val_after_first, val_after_second, 
                         msg=f"{name}: perform_rename() を2回実行した際にサフィックスが二重付与されました。")

    def assert_unique_constraint_cleared(self, factory_class, unique_data):
        """削除後、同じ値で再登録（一意制約の回避）ができるか検証"""
        _, name = self._get_meta(factory_class)
        
        # 1回目作成・削除
        obj = factory_class.create(**unique_data)
        obj.delete()

        # 同じ値で2回目作成（ここで IntegrityError が出なければ成功）
        try:
            factory_class.create(**unique_data)
        except IntegrityError:
            self.fail(f"{name}: 論理削除後の再登録で一意制約エラーが発生しました。リネームが不十分です。")

    def assert_rename_robustness(self, factory_class):
        """存在しないフィールド名が含まれていてもエラーにならないか検証"""
        obj = factory_class.create()
        _, name = self._get_meta(factory_class)
        
        # 一時的に存在しないフィールドをリストに追加
        original_fields = obj.delete_unique_fields
        obj.delete_unique_fields = original_fields + ["non_existent_field_xyz"]
        
        try:
            obj.perform_rename()
        except Exception as e:
            self.fail(f"{name}: 存在しないフィールドが delete_unique_fields にある際に例外が発生しました: {e}")
        finally:
            obj.delete_unique_fields = original_fields