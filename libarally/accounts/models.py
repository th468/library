from django.db import models
from django.contrib.auth.models import(
    BaseUserManager,AbstractBaseUser,PermissionsMixin
)

class UserManager(BaseUserManager):

    def create_user(self, email, em_num, password=None, **extra_fields):
        if not email:
            raise ValueError("メールアドレスは必須です")
        if not em_num:
            raise ValueError("社員番号は必須です")
        email = self.normalize_email(email)
        user = self.model(email=email, em_num=em_num, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, em_num, password=None, **extra_fields ):
        extra_fields["is_staff"] = True
        extra_fields["is_active"] = True
        extra_fields["is_superuser"] = True
        return self.create_user(email, em_num, password, **extra_fields)
    




class User(AbstractBaseUser,PermissionsMixin):

    em_num = models.CharField(max_length=150)
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects= UserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["em_num"]

    def __str__(self):
        return self.email
    