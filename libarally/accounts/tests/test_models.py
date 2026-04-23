from django.test import TestCase
from django.contrib.auth import get_user_model
from ..factories import UserFactory

User = get_user_model()

class UserModelTest(TestCase):
    def test_create_user_success(self):
        """正しい引数でユーザーが作成されるか"""
        user = UserFactory(email="test@example.com", em_num="TEST001")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("password123"))
        self.assertTrue(user.is_active)

    def test_create_superuser_flags(self):
        """スーパーユーザーのフラグが正しいか"""
        admin = User.objects.create_superuser(
            email="admin@example.com", 
            em_num="ADMIN001", 
            password="adminpassword"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_str_method(self):
        """__str__がemailを返すか"""
        user = UserFactory(email="test@example.com")
        self.assertEqual(str(user), "test@example.com")

    def test_can_lend_logic(self):
        """貸出上限のロジックテスト"""
        # 貸出中が0件の場合（lending_limit=5）
        user = UserFactory(lending_limit=5)
        # 本来はLendingのデータが必要だが、まずはメソッドが参照している 
        # active_lending_count が 0 である前提でTrueを確認
        self.assertTrue(user.can_lend())