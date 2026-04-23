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
        user.save(using=self._db) # _dbを指定
        return user
    
    def create_superuser(self, email, em_num, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, em_num, password, **extra_fields)
    




class User(AbstractBaseUser,PermissionsMixin):
    #region フィールド定義
    em_num = models.CharField(
        verbose_name="社員番号", 
        max_length=150, 
        unique=True
        )
    email = models.EmailField(
        verbose_name="メールアドレス", 
        max_length=255, 
        unique=True
        )
    is_active = models.BooleanField(
        verbose_name="有効なユーザーか", 
        default=True
        )
    is_staff = models.BooleanField(
        verbose_name="管理者か",
        default=False)
    
    lending_limit = models.PositiveIntegerField(
        verbose_name="貸出上限冊数", 
        default=5,
        help_text="ユーザーが同時に借りられる最大冊数です。"
    )
    lending_period_days = models.PositiveIntegerField(
        verbose_name="貸出可能日数", 
        default=14,
        help_text="このユーザーが一度の貸出で借りられる日数です。"
    )
    #endregion

    objects= UserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["em_num"]

    def __str__(self):
        return f"従業員番号:{self.em_num}"
    
    @property
    def active_lending_count(self):
        """現在の貸出中件数を返す"""
        # 循環参照を避けるためメソッド内でインポート
        from transactions.models import Lending
        return self.lendings.filter(return_date__isnull=True).count()

    def can_lend(self):
        """貸出可能ならTrue、上限ならFalseを返す"""
        return self.active_lending_count < self.lending_limit

    class Meta:
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"