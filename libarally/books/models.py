from django.db import models, transaction
from django.urls import reverse

#基礎となる抽象モデル
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


"""
    蔵書（実体）モデル
    1つの書誌(Biblio)に対して、複数の実体(Book)が紐付く。
    """
class Book(BaseModel):
    #書籍の状況を表すための定数
    class Status(models.IntegerChoices):
        AVAILABLE = 1, "在庫あり"
        LENT = 2, "貸出中"
        RESERVED = 3, "取り置き中"
        MAINTENANCE = 4, "メンテナンス中"

    biblio = models.ForeignKey(
        "Biblio", 
        on_delete=models.PROTECT, 
        related_name="books", 
        verbose_name="書誌情報",
        help_text="この書籍が属するタイトルの書誌情報"
        )
    shelf = models.ForeignKey(
        "Shelf", 
        on_delete=models.PROTECT,
          related_name="books",
          verbose_name="本棚情報",
          help_text="この書籍が配置されている本棚の情報"
          )
    count =models.PositiveIntegerField(
        "管理番号", 
        editable=False,
        help_text="同一書誌内での通し番号（自動採番）"
        )
    status = models.IntegerField(
        "状況",
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
        help_text="蔵書の状況",
    )

    class Meta:
        verbose_name_plural = "蔵書情報"
        constraints = [
            models.UniqueConstraint(fields=['biblio', 'count'], name='unique_book_copy')
        ]
        ordering = ["-created_at"]


    def __str__(self):
        return f"{self.biblio.title},No.{self.count}"
    def get_absolute_url(self):
        return reverse("books:bookdetail", kwargs={"pk": self.pk})
    
    @property
    def can_be_lent(self):
        return self.status == self.Status.AVAILABLE

    def save(self, *args, **kwargs):
        if not self.pk:
            with transaction.atomic():
                # 同じ書誌に紐づく最新のBookをロックして取得
                last_book = Book.objects.select_for_update().filter(
                    biblio=self.biblio
                ).order_by("-count").first()
                
                self.count = (last_book.count + 1) if last_book else 1
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
    


#書誌情報のモデル
class Biblio(BaseModel):
    isbn = models.CharField(max_length=255, primary_key= True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    price = models.IntegerField
    def __str__(self):
        return self.title
    def get_absolute_url(self):
        return reverse("books:biblio_detail", kwargs={"pk": self.pk})

    class Meta:
        verbose_name_plural = "書誌情報"


#本棚情報のモデル
class Shelf(BaseModel):
    name = models.CharField(max_length=255)
    floor = models.ForeignKey("Floor", on_delete=models.PROTECT, related_name="shelf")
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "本棚情報"

#階情報のモデル
class Floor(BaseModel):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "階情報"








