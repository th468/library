from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.factories import DepartmentFactory, UserFactory
from accounts.forms import ProfileEditForm, UserCreationForm, UserLoginForm

User = get_user_model()


class UserCreationFormTest(TestCase):
    """
    ユーザー登録フォーム (UserCreationForm) のテスト
    """

    def test_form_valid_data(self):
        """有効なデータでのバリデーション成功"""
        form_data = {
            "em_num": "EM999",
            "email": "valid@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        form = UserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_email_duplicate(self):
        """メールアドレス重複時のバリデーション失敗"""
        UserFactory(email="duplicate@example.com")
        form_data = {
            "em_num": "EM001",
            "email": "duplicate@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"][0], "このメールアドレスは既に登録されています。")

    def test_form_invalid_em_num_missing(self):
        """社員番号が欠落している場合のバリデーション失敗"""
        form_data = {
            "email": "missing_em@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("em_num", form.errors)


class ProfileEditFormTest(TestCase):
    """
    プロフィール編集フォーム (ProfileEditForm) のテスト
    """

    def setUp(self):
        self.department = DepartmentFactory(name="開発部")

    def test_form_valid_data(self):
        """有効なデータでのバリデーション成功"""
        form_data = {
            "name": "修正後の名前",
            "department": self.department.pk,
        }
        form = ProfileEditForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_department_empty_label(self):
        """部署選択の初期ラベルが正しく設定されているか"""
        form = ProfileEditForm()
        self.assertEqual(form.fields["department"].empty_label, "部署を選択してください")


class UserLoginFormTest(TestCase):
    """
    ログインフォーム (UserLoginForm) のテスト
    """

    def test_form_widget_attributes(self):
        """ウィジェットの属性（placeholder等）が正しく設定されているか"""
        form = UserLoginForm()
        email_widget = form.fields["username"].widget
        password_widget = form.fields["password"].widget

        self.assertEqual(email_widget.attrs["placeholder"], "example@company.com")
        self.assertTrue(email_widget.attrs["autofocus"])
        self.assertEqual(password_widget.attrs["placeholder"], "パスワードを入力")
