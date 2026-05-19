from django.urls import path

from . import views

app_name = "books"


urlpatterns = [
    path("",views.index, name="index"),
    path("book/", views.BookListView.as_view(), name="booklist"),
    # path("book/detail/<int:pk>/", views.BookDetailView.as_view(), name="bookdetail"),
    # path("manage/index/", views.ManageIndexView.as_view(), name="manageindex"),
    # path("manage/book/create/", views.BookCreateView.as_view(), name="book_create"),
    # path("manage/book/update/<int:pk>/", views.BookUpdateView.as_view(), name="book_update"),
    # path("manage/book/delete/<int:pk>/", views.BookDeleteView.as_view(), name="book_delete"),
    path("manage/biblio/list/", views.BiblioListView.as_view(), name="biblio_list"),
    path("biblio/detail/<int:pk>/", views.BiblioDetailView.as_view(), name="biblio_detail"),
    path("manage/biblio/create/", views.BiblioCreateView.as_view(), name="biblio_create"),
    path("manage/biblio/update/<int:pk>/", views.BiblioUpdateView.as_view(), name="biblio_update"),
    path("manage/biblio/delete/<int:pk>/", views.BiblioDeleteView.as_view(), name="biblio_delete"),
]
