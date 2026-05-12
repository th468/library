from django.db import models

class BaseQuerySet(models.QuerySet):
    """プロジェクト共通のクエリ操作"""
    def delete(self):
        """バルク削除 (queryset.delete()) を論理削除に書き換え"""
        return super().update(is_active=False)

    def hard_delete(self):
        """物理削除を行いたい場合に使用"""
        return super().delete()

    def active(self):
        """有効なデータのみ"""
        return self.filter(is_active=True)

class BaseManager(models.Manager.from_queryset(BaseQuerySet)):
    """
    from_queryset で生成したクラスを継承することで、
    QuerySetのメソッドを Manager でも直接呼べるようにしつつ、
    get_queryset でデフォルトのフィルタをかける。
    """
    def get_queryset(self):
        # デフォルトで active() を適用した状態で QuerySet を返す
        return super().get_queryset().active()




class BaseModel(models.Model):
    is_active = models.BooleanField("有効フラグ", default=True)
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)
    remarks = models.TextField("備考", null=True, blank=True)

    delete_unique_fields = []

    objects = BaseManager()
    all_objects = BaseQuerySet.as_manager()

    class Meta:
        abstract = True

    def __str__(self):
        # 名前かタイトルがあればそれを表示、なければIDを表示
        name = getattr(self, 'title', getattr(self, 'name', ''))
        return f"[{self.pk}] {name}({self.__class__.__name__})" if name else f"[{self.pk}] ({self.__class__.__name__})"
    
    def delete(self, *args, **kwargs):
        from .mixins import RenameUniqueFieldsMixin
        """個別の削除 (instance.delete()) を論理削除に書き換え"""
        self.is_active = False

        if isinstance(self, RenameUniqueFieldsMixin):
            self.perform_rename()
        
        self.save(using=kwargs.get('using'))

    def hard_delete(self):
        """物理削除を行いたい場合に使用"""
        super().delete()
