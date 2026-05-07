from django.db import models
import datetime

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
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def __str__(self):
        # 名前かタイトルがあればそれを表示、なければIDを表示
        name = getattr(self, 'title', getattr(self, 'name', ''))
        return f"[{self.pk}] {name}" if name else f"[{self.pk}] {self.__class__.__name__}"
    
    def delete(self, *args, **kwargs):
        """個別の削除 (instance.delete()) を論理削除に書き換え"""
        self.is_active = False

        # 子クラスで指定されたフィールドがあれば、一括でリネームを実行
        for field_name in self.delete_unique_fields:
            if hasattr(self, field_name):
                self._apply_delete_suffix(field_name)
        
        self.save(using=kwargs.get('using'))

    def _apply_delete_suffix(self, field_name):
        current_val = getattr(self, field_name)
        # すでに削除済みサフィックスがついていないかチェック（二重付与防止）
        if "_del_" not in str(current_val):
            now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            setattr(self, field_name, f"{current_val}_del_{now}")

    def hard_delete(self):
        """物理削除を行いたい場合に使用"""
        super().delete()
