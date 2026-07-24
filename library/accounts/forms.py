from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()


class UserCreationForm(DjangoUserCreationForm):
    """
    ユーザー登録用フォーム
    カスタムユーザーモデルに対応
    """

    class Meta:
        model = User
        fields = ("em_num", "email")
        field_classes = {"email": UsernameField}

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("このメールアドレスは既に登録されています。")
        return email


class ProfileEditForm(forms.ModelForm):
    """
    プロフィール編集用フォーム
    """

    class Meta:
        model = User
        fields = ("name", "department")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "department" in self.fields:
            self.fields["department"].empty_label = "部署を選択してください"


class UserLoginForm(AuthenticationForm):
    """
    ログイン用フォーム
    Django標準のLoginViewに適合させるためAuthenticationFormを継承
    """

    username = forms.EmailField(
        label="メールアドレス",
        max_length=255,
        widget=forms.EmailInput(attrs={"placeholder": "example@company.com", "autofocus": True}),
    )
    password = forms.CharField(
        label="パスワード", widget=forms.PasswordInput(attrs={"placeholder": "パスワードを入力"})
    )
