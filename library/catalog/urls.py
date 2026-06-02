from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    # ユーザー用（公開画面）
    path("list/", views.BiblioSearchListView.as_view(), name="booklist"),
    path("detail/<int:pk>/", views.BiblioDetailView.as_view(), name="bookdetail"),
    path("favorite/<int:pk>/", views.FavoriteToggleView.as_view(), name="favorite_toggle"),

    # 管理用（スタッフ専用）
    path("manage/", views.ManageIndexView.as_view(), name="manageindex"),
]
