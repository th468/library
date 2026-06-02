from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView
from catalog.models import Biblio
from transactions.models import Lending
from core.views.mixins import PageTitleMixin

class DashboardIndexView(TemplateView):
    """
    サイトトップ / ダッシュボード
    ログイン状況に応じて「紹介ページ」と「ユーザー専用ダッシュボード」を出し分ける。
    """
    
    def get_template_names(self):
        # ログイン状態によって使用するテンプレートを動的に切り替え
        if self.request.user.is_authenticated:
            return ["dashboard/index.html"]
        return ["dashboard/landing.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ログイン済みの場合のみ、ダッシュボード用のデータを取得
        if self.request.user.is_authenticated:
            # ユーザー共通の情報（新着本など）を取得
            context['recent_biblios'] = Biblio.objects.all().order_by('-created_at')[:5]
            # お気に入り登録した本を取得（最新5件）
            context['favorite_biblios'] = self.request.user.favorite_biblios[:5]
        
        return context


class LendingHistoryView(LoginRequiredMixin, PageTitleMixin, ListView):
    """
    貸出履歴の全件表示
    """
    model = Lending
    template_name = "dashboard/history_list.html"
    context_object_name = "history_list"
    paginate_by = 10
    page_title = "貸出履歴"

    def get_queryset(self):
        # 自身の返却済み貸出履歴を新しい順に取得
        return (
            self.request.user.lending_set.returned()
            .select_related("book__biblio")
            .order_by("-return_date")
        )
