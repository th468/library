from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..factories import DepartmentFactory, UserFactory

User = get_user_model()


class UserAccountViewsTest(TestCase):
    """
    アカウント関連のビュー（ログイン、登録、プロフィール編集等）のテスト
    """

    def setUp(self):
        self.department = DepartmentFactory(name="技術部")
        self.user = UserFactory(
            email="test@example.com", em_num="EM001", name="テスト太郎", department=self.department
        )
        self.user.set_password("password123")
        self.user.save()

    # --- 1. ログイン/ログアウト ---

    def test_login_view_get(self):
        """ログイン画面の表示確認"""
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_login_success(self):
        """正常なログイン"""
        # UserLoginForm は AuthenticationForm 継承なのでフィールド名は username
        response = self.client.post(
            reverse("accounts:login"), {"username": "test@example.com", "password": "password123"}
        )
        self.assertRedirects(response, reverse("dashboard:index"))
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_login_fail(self):
        """間違ったパスワードでのログイン失敗"""
        response = self.client.post(
            reverse("accounts:login"), {"username": "test@example.com", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse("_auth_user_id" in self.client.session)
        # フォームエラーが表示されているか確認
        self.assertContains(response, "メールアドレス")
        self.assertContains(response, "パスワード")

    def test_logout(self):
        """ログアウト機能の確認"""
        self.client.login(email="test@example.com", password="password123")
        # Django 5.0+ では LogoutView は POST がデフォルト
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertFalse("_auth_user_id" in self.client.session)

    # --- 2. ユーザー登録 ---

    def test_registration_view_get(self):
        """登録画面の表示確認"""
        response = self.client.get(reverse("accounts:regist"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/registration.html")

    def test_registration_success(self):
        """正常なユーザー登録"""
        response = self.client.post(
            reverse("accounts:regist"),
            {
                "em_num": "NEW001",
                "email": "new@example.com",
                "password1": "newpassword123",
                "password2": "newpassword123",
            },
        )
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_registration_email_duplicate(self):
        """メールアドレス重複時のエラー"""
        response = self.client.post(
            reverse("accounts:regist"),
            {
                "em_num": "NEW001",
                "email": "test@example.com",  # 既に存在するemail
                "password1": "newpassword123",
                "password2": "newpassword123",
            },
        )
        self.assertEqual(response.status_code, 200)
        # assertFormError の第1引数に直接フォームオブジェクトを渡す
        self.assertFormError(response.context["form"], "email", "このメールアドレスは既に登録されています。")

    # --- 3. プロフィール機能 (LoginRequired) ---

    def test_profile_detail_view_login_required(self):
        """未ログイン時は詳細画面にアクセスできない"""
        response = self.client.get(reverse("accounts:profile_detail"))
        # login_url が /accounts/login/ なので、そちらへリダイレクトされる
        expected_url = f"{reverse('accounts:login')}?next={reverse('accounts:profile_detail')}"
        self.assertRedirects(response, expected_url)

    def test_profile_detail_view_success(self):
        """ログイン時は詳細画面が表示される"""
        self.client.login(email="test@example.com", password="password123")
        response = self.client.get(reverse("accounts:profile_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile_detail.html")
        self.assertContains(response, "テスト太郎")
        self.assertContains(response, "技術部")

    def test_profile_edit_success(self):
        """プロフィールの更新成功"""
        self.client.login(email="test@example.com", password="password123")
        new_department = DepartmentFactory(name="人事部")
        response = self.client.post(
            reverse("accounts:profile_edit"), {"name": "更新後の名前", "department": new_department.pk}
        )
        self.assertRedirects(response, reverse("accounts:profile_detail"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "更新後の名前")
        self.assertEqual(self.user.department, new_department)

    # --- 4. パスワード変更 ---

    def test_password_change_success(self):
        """パスワード変更の成功"""
        self.client.login(email="test@example.com", password="password123")
        response = self.client.post(
            reverse("accounts:password_change"),
            {"old_password": "password123", "new_password1": "newpass45678", "new_password2": "newpass45678"},
        )
        self.assertRedirects(response, reverse("accounts:password_change_done"))

        # 新しいパスワードでログインできるか確認
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass45678"))

    def test_password_change_fail_wrong_old_password(self):
        """パスワード変更失敗：古いパスワードが間違っている場合"""
        self.client.login(email="test@example.com", password="password123")
        response = self.client.post(
            reverse("accounts:password_change"),
            {"old_password": "wrongpassword", "new_password1": "newpass45678", "new_password2": "newpass45678"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "old_password",
            "元のパスワードが間違っています。もう一度入力してください。",
        )

    def test_password_change_fail_mismatched_new_passwords(self):
        """パスワード変更失敗：新しいパスワード（確認用）が一致しない場合"""
        self.client.login(email="test@example.com", password="password123")
        response = self.client.post(
            reverse("accounts:password_change"),
            {"old_password": "password123", "new_password1": "newpass45678", "new_password2": "mismatch45678"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "new_password2", "確認用パスワードが一致しません。")

    def test_password_change_fail_weak_password(self):
        """パスワード変更失敗：脆弱な（短すぎる）パスワードの場合"""
        self.client.login(email="test@example.com", password="password123")
        response = self.client.post(
            reverse("accounts:password_change"),
            {"old_password": "password123", "new_password1": "123", "new_password2": "123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "短すぎます")
