from datetime import timedelta

from core.models.mixins import RenameUniqueFieldsMixin


class BaseModelBehaviorMixin:
    """BaseModelの基本機能を検証するためのツールキット"""

    def _get_meta(self, factory):
        model = factory._meta.model
        return model, model.__name__

    def assert_managers_strictly_separated(self, factory):
        """objects(有効) と all_objects(全件) の分離を検証"""
        model, name = self._get_meta(factory)
        factory.create(is_active=True)
        factory.create(is_active=False)

        self.assertEqual(model.objects.count(), 1, msg=f"{name}: objects に無効データが含まれています。")
        self.assertEqual(model.all_objects.count(), 2, msg=f"{name}: all_objects で全件取得できていません。")
        self.assertEqual(
            model.objects.filter(is_active=False).count(),
            0,
            msg=f"{name}: objects.filter(is_active=False) がデータを返しました。",
        )

    def assert_logical_delete_instance(self, factory):
        """インスタンスの delete() による論理削除を検証"""
        model, name = self._get_meta(factory)
        obj = factory.create()

        # delete() による更新を即座に判定できるよう、DB上の updated_at を一時的に過去時刻に設定
        past_time = obj.updated_at - timedelta(seconds=10)
        model.all_objects.filter(pk=obj.pk).update(updated_at=past_time)
        old_updated_at = past_time

        # 実行
        obj.delete()
        obj.refresh_from_db()

        self.assertFalse(obj.is_active, msg=f"{name}: delete() 後に is_active が False になっていません。")
        self.assertGreater(
            obj.updated_at, old_updated_at, msg=f"{name}: delete() 後に updated_at が更新されていません。"
        )
        self.assertFalse(
            model.objects.filter(pk=obj.pk).exists(), msg=f"{name}: 論理削除されたデータが objects に残っています。"
        )

    def assert_logical_delete_queryset(self, factory):
        """QuerySet.delete() によるバルク論理削除を検証"""
        model, name = self._get_meta(factory)
        # テスト開始前にDBを完全に空にする
        model.all_objects.all().hard_delete()
        factory.create_batch(3)

        # 実行
        res = model.objects.all().delete()

        self.assertIsInstance(res, int, msg=f"{name}: QuerySet.delete() の戻り値が更新件数(int)ではありません。")
        self.assertEqual(model.objects.count(), 0, msg=f"{name}: バルク削除後、objects にデータが残っています。")
        self.assertEqual(
            model.all_objects.filter(is_active=False).count(),
            3,
            msg=f"{name}: バルク削除されたデータが all_objects に正しく反映されていません。",
        )

    def assert_hard_delete_behavior(self, factory):
        """hard_delete() による物理削除を検証"""
        model, name = self._get_meta(factory)

        # インスタンスレベル
        obj = factory.create()
        obj.hard_delete()
        self.assertFalse(
            model.all_objects.filter(pk=obj.pk).exists(), msg=f"{name}: インスタンスの物理削除に失敗しました。"
        )

        # クエリセットレベル
        factory.create_batch(2)
        model.all_objects.all().hard_delete()
        self.assertEqual(model.all_objects.count(), 0, msg=f"{name}: クエリセットの物理削除に失敗しました。")

    def assert_base_model_logic(self, factory):
        """共通フィールド(created_at, remarks)の保存を検証"""
        model, name = self._get_meta(factory)

        # remarksの保存確認
        obj = factory.create(remarks="Test Remarks")
        self.assertIsNotNone(obj.created_at, msg=f"{name}: created_at が自動付与されていません。")
        self.assertEqual(obj.remarks, "Test Remarks", msg=f"{name}: remarks が正しく保存されていません。")


class RenameUniqueTestMixin:
    """リネーム機能 (RenameUniqueFieldsMixin) を検証するためのツールキット"""

    def assert_rename_works(self, factory, unique_fields):
        """サフィックス付与の正確性を検証"""
        model, name = self._get_meta(factory)
        obj = factory.create()
        original_values = {field: getattr(obj, field) for field in unique_fields}

        obj.delete()
        obj.refresh_from_db()

        for field in unique_fields:
            new_val = getattr(obj, field)
            self.assertIn(
                "_del_", str(new_val), msg=f"{name}: フィールド {field} にサフィックスが付与されていません。"
            )
            self.assertTrue(
                str(new_val).startswith(str(original_values[field])),
                msg=f"{name}: フィールド {field} の元の値が保持されていません。",
            )

    def assert_double_rename_protection(self, factory, unique_fields):
        """二重リネームの防止を検証"""
        obj = factory.create()
        obj.delete()  # 1回目
        obj.refresh_from_db()
        val_after_first_delete = {field: getattr(obj, field) for field in unique_fields}

        obj.perform_rename()  # 2回目を手動実行

        for field in unique_fields:
            self.assertEqual(
                getattr(obj, field),
                val_after_first_delete[field],
                msg=f"{factory._meta.model.__name__}: 二重リネームによりサフィックスが重複付与されました。",
            )

    def assert_unique_constraint_cleared(self, factory, unique_test_data):
        """削除後の再登録成功を検証"""
        model, name = self._get_meta(factory)
        # 一度作成して削除
        obj = factory.create(**unique_test_data)
        obj.delete()

        # 同じ値で再作成（ユニーク制約エラーが起きないことを確認）
        try:
            factory.create(**unique_test_data)
        except Exception as e:
            self.fail(
                msg=f"{name}: 削除済データのユニーク制約が解放されていないため、再登録に失敗しました。 エラー: {e}"
            )

    def assert_rename_robustness(self, factory):
        """存在しないフィールド指定時のエラー耐性を検証"""
        model, name = self._get_meta(factory)
        obj = factory.create()
        # 存在しないフィールドを一時的に追加
        obj.delete_unique_fields.append("non_existent_field")

        try:
            obj.delete()
        except Exception as e:
            self.fail(
                msg=f"{name}: 存在しないフィールドが delete_unique_fields に含まれるとエラーが発生します。 エラー: {e}"
            )


class BaseModelTestMixin(BaseModelBehaviorMixin, RenameUniqueTestMixin):
    """
    全てのモデルテストの基底となるクラス。
    factory_class を定義するだけで、標準的な全テストを自動実行する。
    """

    factory_class = None
    unique_fields = []
    unique_test_data = {}
    skip_rename_test = False

    def test_standard_behavior(self):
        """サブテストを利用した一括検証ランナー"""
        if not self.factory_class:
            return

        f = self.factory_class
        model, name = self._get_meta(f)

        # 実行前にDBをクリーンアップ
        model.all_objects.all().hard_delete()

        # 1. 共通コア機能テスト
        core_cases = [
            ("ManagersSeparation", self.assert_managers_strictly_separated),
            ("LogicalDeleteInstance", self.assert_logical_delete_instance),
            ("LogicalDeleteQuerySet", self.assert_logical_delete_queryset),
            ("HardDeleteBehavior", self.assert_hard_delete_behavior),
            ("BaseModelLogic", self.assert_base_model_logic),
        ]

        for label, method in core_cases:
            with self.subTest(check=label, model=name):
                method(f)

        # 2. Rename機能の自動判定実行
        if issubclass(model, RenameUniqueFieldsMixin) and not self.skip_rename_test:
            rename_cases = [
                ("RenameWorks", lambda factory: self.assert_rename_works(factory, self.unique_fields)),
                (
                    "DoubleRenameProtection",
                    lambda factory: self.assert_double_rename_protection(factory, self.unique_fields),
                ),
                (
                    "UniqueConstraintCleared",
                    lambda factory: self.assert_unique_constraint_cleared(factory, self.unique_test_data),
                ),
                ("RenameRobustness", self.assert_rename_robustness),
            ]
            for label, method in rename_cases:
                with self.subTest(check=f"Rename:{label}", model=name):
                    method(f)

        # 3. __str__ の検証（フックメソッド）
        with self.subTest(check="StringRepresentation", model=name):
            self.run_str_test()

    def run_str_test(self):
        """__str__ の検証ロジック（必要に応じてオーバーライド可能）"""
        f = self.factory_class
        model, name = self._get_meta(f)

        # 1. 名前がある場合のテスト
        create_kwargs = {}
        expected_part = ""
        if hasattr(model, "title"):
            create_kwargs["title"] = "TestTitle"
            expected_part = "TestTitle"
        elif hasattr(model, "name"):
            create_kwargs["name"] = "TestName"
            expected_part = "TestName"

        if expected_part:
            obj = f.create(**create_kwargs)
            display_str = str(obj)
            self.assertIn(
                expected_part,
                display_str,
                msg=f"{name}: __str__ に期待される文字列({expected_part})が含まれていません。",
            )

        # 2. 名前がない場合のテスト（PK の表示を要求）
        # 名前/タイトルフィールドを空にして作成
        empty_kwargs = {
            k: ""
            for k in (["title"] if hasattr(model, "title") else []) + (["name"] if hasattr(model, "name") else [])
        }
        obj_no_name = f.create(**empty_kwargs)
        display_str_no_name = str(obj_no_name)
        self.assertIn(
            str(obj_no_name.pk),
            display_str_no_name,
            msg=f"{name}: 名前がない場合の __str__ に PK が含まれていません。",
        )
