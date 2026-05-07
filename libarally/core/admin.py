from django.contrib import admin
from django.utils.translation import gettext_lazy as _

class ActiveFilter(admin.SimpleListFilter):
    """「有効 / 削除済み / すべて」を切り替えるフィルター"""
    title = _('有効ステータス')
    parameter_name = 'is_active_status'

    def lookups(self, request, model_admin):
        return (
            ('active', _('有効のみ')),
            ('deleted', _('削除済みのみ')),
            ('all', _('すべて')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True)
        if self.value() == 'deleted':
            return queryset.filter(is_active=False)
        if self.value() == 'all':
            return queryset
        # デフォルトは有効のみ表示
        return queryset.filter(is_active=True)
    
class BaseLogicalDeleteAdmin(admin.ModelAdmin):
    # 共通の表示設定（必要に応じて子クラスで上書き）
    list_display = ('__str__', 'is_active_display', 'created_at')
    list_filter = (ActiveFilter,)
    
    # 1. 管理画面では「削除済み」も含めて表示する
    def get_queryset(self, request):
        return self.model.all_objects.get_queryset()

    # 2. 個別削除ボタンを「論理削除」に書き換え
    def delete_model(self, request, obj):
        obj.delete()

    # 3. チェックボックスによる一括削除を「論理削除」に書き換え
    def delete_queryset(self, request, queryset):
        queryset.delete()

    # 4. アクションの制御
    def get_actions(self, request):
        actions = super().get_actions(request)
        # スーパーユーザー以外からは「物理削除（delete_selected）」を消す
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions

    # 5. 「復元」アクションの追加
    actions = ['restore_selected']

    @admin.action(description="選択されたデータを復元する")
    def restore_selected(self, request, queryset):
        updated_count = queryset.update(is_active=True)
        self.message_user(request, f"{updated_count} 件のデータを復元しました。")

    # 6. 見た目の工夫：削除済みを赤文字にする
    @admin.display(description="ステータス", boolean=True)
    def is_active_display(self, obj):
        return obj.is_active
