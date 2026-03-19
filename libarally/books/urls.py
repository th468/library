from django.urls import path
from . import views

app_name = "books"


urlpatterns = [
    path("",views.index, name="index"),
    path("book/", views.BookListView.as_view(), name="booklist"),
    path("book/detail/<int:pk>/", views.BookDetailView.as_view(), name="bookdetail"),
    path("manage/index/", views.ManageIndexView.as_view(), name="manageindex"),
    path("manage/book/create/", views.BookCreateView.as_view(), name="book_create"),
    path("manage/biblio/create/", views.BiblioCreateView.as_view(), name="biblio_create"),
]