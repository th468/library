from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from unittest.mock import PropertyMock, patch

from ..models import User, Department
from ..factories import UserFactory, DepartmentFactory


class UserManagerTest(TestCase):
    """
    UserManagerの生成ロジックそのものをテストするクラス
    """
    def test_create_user_success(self):
        """create_user で正常に作成され、パスワードが暗号化されているか"""
        email = "test@example.com"
        em_num = "EM001"
        password = "password123"
        user = User.objects.create_user(
            email=email,
            em_num=em_num,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertEqual(user.em_num, em_num)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser_success(self):
        """create_superuser で適切な権限フラグが立っているか"""
        user = User.objects.create_superuser(
            email="admin@example.com",
            em_num="ADMIN01",
            password="adminpassword"
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_user_fail(self):
        """必須引数（email, em_num）が欠落した際に ValueError が発生するか"""
        with self.assertRaisesRegex(ValueError, "メールアドレスは必須です"):
            User.objects.create_user(email="", em_num="EM001", password="pw")
        
        with self.assertRaisesRegex(ValueError, "社員番号は必須です"):
            User.objects.create_user(email="test@example.com", em_num="", password="pw")


class UserModelTest(TestCase):
    """
    Userモデルの定義と振る舞いをテストするクラス
    """
    # --- ① 共通テスト項目 ---

    def test_create_success(self):
        """Factoryでエラーなくインスタンスが作成・保存できるか"""
        user = UserFactory()
        self.assertIsInstance(user, User)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_str_representation(self):
        """__str__ が期待通りの値を返すか"""
        user = UserFactory(em_num="TEST-001")
        self.assertEqual(str(user), "従業員番号:TEST-001")

    def test_required_fields(self):
        """各必須項目を空にして full_clean() を呼んだ際、ValidationError が出るか"""
        user = UserFactory()
        user.email = ""
        user.em_num = ""
        with self.assertRaises(ValidationError) as cm:
            user.full_clean()
        self.assertIn('email', cm.exception.message_dict)
        self.assertIn('em_num', cm.exception.message_dict)

    def test_unique_constraint(self):
        """unique=True の項目が重複した際、full_clean() で ValidationError が出るか"""
        UserFactory(email="dup@example.com", em_num="DUP001")
        duplicate_user = UserFactory.build(email="dup@example.com", em_num="DUP001")
        with self.assertRaises(ValidationError) as cm:
            duplicate_user.full_clean()
        self.assertIn('email', cm.exception.message_dict)
        self.assertIn('em_num', cm.exception.message_dict)

    def test_max_length_constraint(self):
        """max_length を超える文字列を代入し full_clean() でエラーが出るか"""
        user = UserFactory()
        user.em_num = "a" * 151
        user.email = ("a" * 250) + "@example.com"  # 255超
        with self.assertRaises(ValidationError) as cm:
            user.full_clean()
        self.assertIn('em_num', cm.exception.message_dict)
        self.assertIn('email', cm.exception.message_dict)

    # --- ② 個別テスト項目 (can_lend) ---

    def test_can_lend_normal(self):
        """正常系: 貸出中件数が上限未満ならTrueを返す"""
        user = UserFactory(lending_limit=5)
        # active_lending_count プロパティを Mock 化
        with patch('accounts.models.User.active_lending_count', new_callable=PropertyMock) as mock_count:
            mock_count.return_value = 0
            self.assertTrue(user.can_lend)
            
            mock_count.return_value = 4
            self.assertTrue(user.can_lend)

    def test_can_lend_abnormal(self):
        """異常系: 貸出中件数が上限を超えている（想定外だがロジック上）場合はFalseを返す"""
        user = UserFactory(lending_limit=5)
        with patch('accounts.models.User.active_lending_count', new_callable=PropertyMock) as mock_count:
            mock_count.return_value = 6
            self.assertFalse(user.can_lend)

    def test_can_lend_boundary(self):
        """境界値: 貸出中件数が上限と一致する場合、Falseを返す"""
        user = UserFactory(lending_limit=5)
        with patch('accounts.models.User.active_lending_count', new_callable=PropertyMock) as mock_count:
            mock_count.return_value = 5
            self.assertFalse(user.can_lend)


class DepartmentModelTest(TestCase):
    """
    Departmentモデルの定義と振る舞いをテストするクラス
    """
    def test_create_success(self):
        """Factoryでエラーなくインスタンスが作成・保存できるか"""
        dept = DepartmentFactory()
        self.assertIsInstance(dept, Department)

    def test_str_representation(self):
        """__str__ が期待通りの値を返すか"""
        dept = DepartmentFactory(name="開発部")
        self.assertEqual(str(dept), "開発部")

    def test_required_fields(self):
        """必須項目を空にして full_clean() を呼んだ際、ValidationError が出るか"""
        dept = DepartmentFactory()
        dept.name = ""
        with self.assertRaises(ValidationError):
            dept.full_clean()

    def test_max_length_constraint(self):
        """max_length(255) を超える文字列を代入し full_clean() でエラーが出るか"""
        dept = DepartmentFactory()
        dept.name = "a" * 256
        with self.assertRaises(ValidationError):
            dept.full_clean()