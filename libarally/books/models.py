from django.db import models
from django.urls import reverse
from django.conf import settings

#基礎となる抽象モデル
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


#蔵書情報のモデル
class Book(BaseModel):
    biblio = models.ForeignKey("Biblio", on_delete=models.PROTECT, related_name="book")
    shelf = models.ForeignKey("Shelf", on_delete=models.PROTECT, related_name="book")
    count =models.IntegerField(editable=False)
    is_available = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.biblio.title},{self.count}"
    def get_absolute_url(self):
        return reverse("books:bookdetail", kwargs={"pk": self.pk})
    #　書籍登録時に既に同一の書誌情報を持つ書籍が存在する場合、countを自動的に増加させる
    def save(self, *args, **kwargs):
        if not self.pk:
            last_book = Book.objects.filter(biblio=self.biblio).order_by("-count").first()
            if last_book:
                self.count = last_book.count + 1
            else:
                self.count = 1

        super().save(*args, **kwargs)
        

    class Meta:
        verbose_name_plural = "蔵書情報"
        unique_together = ("biblio", "count")
    

#書誌情報のモデル
class Biblio(BaseModel):
    isbn = models.CharField(max_length=255, primary_key= True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    price = models.IntegerField
    is_available = models.BooleanField(default=True)
    def __str__(self):
        return self.title

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








