import datetime

class RenameUniqueFieldsMixin:    
    delete_unique_fields = []
    def perform_rename(self):

        # 子クラスで指定されたフィールドがあれば、一括でリネームを実行
        for field_name in self.delete_unique_fields:
            if hasattr(self, field_name):
                self._apply_delete_suffix(field_name)

    def _apply_delete_suffix(self, field_name):
        current_val = getattr(self, field_name)
        # すでに削除済みサフィックスがついていないかチェック（二重付与防止）
        if "_del_" not in str(current_val):
            now = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
            setattr(self, field_name, f"{current_val}_del_{now}")
