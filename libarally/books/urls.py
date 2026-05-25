from django.urls import path
from . import views

app_name = "books"

urlpatterns = [
    # ユーザー用（公開画面）
    path("list/", views.BiblioSearchListView.as_view(), name="booklist"),
    path("detail/<int:pk>/", views.BiblioDetailView.as_view(), name="biblio_detail"),

    # 管理用（スタッフ専用）
    path("manage/", views.ManageIndexView.as_view(), name="manageindex"),
    path("manage/biblio/", views.ManageBiblioListView.as_view(), name="biblio_list"),
    path("manage/biblio/detail/<int:pk>/", views.ManageBiblioDetailView.as_view(), name="biblio_manage_detail"),
    path("manage/biblio/create/", views.BiblioCreateView.as_view(), name="bibliocreate"),
    path("manage/biblio/update/<int:pk>/", views.BiblioUpdateView.as_view(), name="biblioupdate"),
    path("manage/biblio/delete/<int:pk>/", views.BiblioDeleteView.as_view(), name="bibliodelete"),
    path("manage/shelf/", views.ShelfListView.as_view(), name="shelflist"),
    path("manage/floor/", views.FloorListView.as_view(), name="floorlist"),
    path("manage/floor/detail/<int:pk>/", views.FloorDetailView.as_view(), name="floordetail"),
]
