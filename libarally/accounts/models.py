from core.models.base import BaseModel
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, em_num, password=None, **extra_fields):
        if not email:
            raise ValueError("メールアドレスは必須です")
        if not em_num:
            raise ValueError("社員番号は必須です")

        email = self.normalize_email(email)
        user = self.model(email=email, em_num=em_num, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)  # _dbを指定
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


class User(AbstractBaseUser, PermissionsMixin):
    # region フィールド定義
    em_num = models.CharField(verbose_name="社員番号", max_length=150, unique=True)
    email = models.EmailField(verbose_name="メールアドレス", max_length=255, unique=True)
    is_active = models.BooleanField(verbose_name="有効なユーザーか", default=True)
    is_staff = models.BooleanField(verbose_name="管理者か", default=False)
    lending_limit = models.PositiveIntegerField(
        verbose_name="貸出上限冊数", default=5, help_text="ユーザーが同時に借りられる最大冊数です。"
    )
    lending_period_days = models.PositiveIntegerField(
        verbose_name="貸出可能日数", default=14, help_text="このユーザーが一度の貸出で借りられる日数です。"
    )
    name = models.CharField(
        verbose_name="氏名",
        max_length=255,
        null=True,
        blank=True,
    )
    department = models.ForeignKey(
        "Department",
        verbose_name="部署",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # BaseModel と同等の管理用フィールドを個別追加（認証系との競合を避けるため継承はしない）
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)
    remarks = models.TextField("備考", null=True, blank=True)

    # endregion

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["em_num"]

    def __str__(self):
        return f"従業員番号:{self.em_num}"

    @property
    def active_lending_count(self):
        """現在の貸出中件数を返す"""
        # 循環参照を避けるためメソッド内でインポート
        return self.lending_set.filter(return_date__isnull=True).count()

    @property
    def can_lend(self):
        """貸出可能ならTrue、上限ならFalseを返す"""
        return self.active_lending_count < self.lending_limit

    @property
    def has_overdue_loans(self):
        """このユーザーに1件でも延滞があるか"""
        # LendingのManager経由でQuerySetのoverdue()を呼び出す
        return self.lending_set.overdue().exists()

    @property
    def active_lendings(self):
        """自身の有効な貸出リスト（期限の近い順）"""
        return self.lending_set.active().select_related("book__biblio").order_by("due_date")

    @property
    def active_reservations(self):
        """自身の有効な予約リスト（古い順 ＝ 順番が早くくる順）"""
        return self.reservation_set.active().select_related("biblio").order_by("created_at")

    class Meta:
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"
...


class Department(BaseModel):
    name = models.CharField(
        verbose_name="部署名",
        max_length=255,
    )

    class Meta:
        verbose_name = "部署"
        verbose_name_plural = "部署"
