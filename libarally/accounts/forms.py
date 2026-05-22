from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

User = get_user_model()


# 登録、管理用
class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="パスワード", widget=forms.PasswordInput)
    password2 = forms.CharField(label="パスワード(確認)", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("em_num", "email")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 != password2:
            raise ValidationError("パスワードが一致しません")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data.get("password1"))
        user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="パスワード")

    class Meta:
        model = User
        fields = ("em_num", "email", "password", "is_active", "is_staff", "is_superuser")


# ログイン用
class UserLoginForm(forms.Form):
    email = forms.EmailField(label="メールアドレス", max_length=255)
    password = forms.CharField(label="パスワード", widget=forms.PasswordInput)
