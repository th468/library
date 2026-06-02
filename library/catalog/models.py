from core.models.base import BaseModel
from core.models.mixins import RenameUniqueFieldsMixin
from django.db import models, transaction
from django.urls import reverse


# カテゴリモデル
class Category(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="カテゴリ名")


    class Meta:
        verbose_name_plural = "カテゴリ情報"


# 書誌情報のモデル
class Biblio(BaseModel):
    isbn = models.CharField(max_length=255, unique=True, verbose_name="ISBN")
    title = models.CharField(max_length=255, verbose_name="タイトル")
    subtitle = models.CharField(max_length=255, null=True, blank=True, verbose_name="副題")
    author = models.CharField(max_length=255, verbose_name="著者")
    publisher = models.CharField(max_length=255, verbose_name="出版社")
    published_date = models.CharField(max_length=50, null=True, blank=True, verbose_name="出版日")
    description = models.TextField(null=True, blank=True, verbose_name="内容紹介")
    cover = models.ImageField("書影", upload_to="catalog/covers/", null=True, blank=True)

    # カテゴリとの多対多リレーション
    categories = models.ManyToManyField(Category, blank=True, related_name="biblios", verbose_name="カテゴリ")

    def __str__(self):
        if self.title.strip():
            return f"【書誌】{self.title}"
        return super().__str__()

    def get_absolute_url(self):
        return reverse("catalog:bookdetail", kwargs={"pk": self.pk})

    @property
    def total_count(self):
        """このタイトルの全在庫数を返す"""
        return self.books.count()

    @property
    def available_count(self):
        """現在貸出可能な（在庫あり）冊数を返す"""
        return self.books.filter(status=1).count()  # 1: AVAILABLE

    @property
    def is_available(self):
        """1冊でも貸出可能ならTrue"""
        return self.available_count > 0

    class Meta:
        verbose_name_plural = "書誌情報"


"""
    蔵書（実体）モデル
    1つの書誌(Biblio)に対して、複数の実体(Book)が紐付く。
    """


class Book(BaseModel, RenameUniqueFieldsMixin):
    # 書籍の状況を表すための定数
    class Status(models.IntegerChoices):
        AVAILABLE = 1, "在庫あり"
        LENT = 2, "貸出中"
        RESERVED = 3, "予約中"
        MAINTENANCE = 4, "メンテナンス中"
        LOST = 5, "紛失"

    biblio = models.ForeignKey(
        "Biblio",
        on_delete=models.PROTECT,
        related_name="books",
        verbose_name="書誌情報",
        help_text="この書籍が属するタイトルの書誌情報",
    )
    shelf = models.ForeignKey(
        "Shelf",
        on_delete=models.PROTECT,
        related_name="books",
        verbose_name="本棚情報",
        help_text="この書籍が配置されている本棚の情報",
    )
    count = models.PositiveIntegerField("管理番号", editable=False, help_text="同一書誌内での通し番号（自動採番）")
    status = models.IntegerField("状況", choices=Status.choices, default=Status.AVAILABLE, db_index=True)

    class Meta:
        verbose_name_plural = "蔵書情報"
        constraints = [models.UniqueConstraint(fields=["biblio", "count"], name="unique_book_copy")]
        ordering = ["-created_at"]

    def __str__(self):
        if self.biblio.title.strip():
            return f"【現物】{self.biblio.title} (No.{self.count})"
        return super().__str__()

    # def get_absolute_url(self):
    #     return reverse("catalog:bookdetail", kwargs={"pk": self.pk})

    @property
    def can_be_lent(self):
        return self.status == self.Status.AVAILABLE

    @property
    def can_be_reserved(self):
        """予約対象になり得るか（紛失等を除外）"""
        return self.status in [self.Status.AVAILABLE, self.Status.LENT, self.Status.RESERVED]

    def save(self, *args, **kwargs):
        if not self.pk:
            with transaction.atomic():
                # 同じ書誌に紐づく最新のBookをロックして取得
                last_book = Book.objects.select_for_update().filter(biblio=self.biblio).order_by("-count").first()

                self.count = (last_book.count + 1) if last_book else 1
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


# 本棚情報のモデル
class Shelf(BaseModel):
    name = models.CharField(max_length=255)
    floor = models.ForeignKey("Floor", on_delete=models.PROTECT, related_name="shelf")
    description = models.TextField("場所の詳細説明", null=True, blank=True, help_text="例：南側自動販売機の横、など")
    location_photo = models.ImageField("配置写真", upload_to="catalog/shelves/", null=True, blank=True)

    class Meta:
        verbose_name_plural = "本棚情報"


# 階情報のモデル
class Floor(BaseModel):
    name = models.CharField(max_length=255)
    map = models.ImageField("フロアマップ", upload_to="catalog/maps/", null=True, blank=True)

    class Meta:
        verbose_name_plural = "階情報"


class Favorite(BaseModel):
    """ユーザーと書誌を紐付けるお気に入りモデル"""

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, verbose_name="ユーザー")
    biblio = models.ForeignKey(Biblio, on_delete=models.CASCADE, verbose_name="お気に入り書誌")

    class Meta:
        verbose_name = "お気に入り"
        verbose_name_plural = "お気に入り"
        unique_together = ("user", "biblio")

    def __str__(self):
        return f"【お気に入り】{self.user.email} - {self.biblio.title}"
