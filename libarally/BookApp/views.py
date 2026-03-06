from django.shortcuts import render

from django.views.generic.list import ListView

from .models import Book


class BookListView(ListView):
    queryset = Book.objects.all()
    template_name = "Book_list.html"


def index(request):
    return render(request, "accounts/index.html")