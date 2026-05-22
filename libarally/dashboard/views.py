from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from books.models import Biblio

class DashboardIndexView(LoginRequiredMixin, TemplateView):
    """
    ユーザー専用ダッシュボード
    """
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ユーザー固有の情報は User モデルのプロパティ（user.active_lendings 等）をテンプレートで使用。
        # ここではユーザー共通の情報（新着本など）のみを取得
        context['recent_biblios'] = Biblio.objects.all().order_by('-created_at')[:5]
        
        return context
