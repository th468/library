from django.urls import reverse_lazy
from django.shortcuts import render,redirect
from django.views.generic import ListView,DetailView,TemplateView
from django.views.generic import CreateView
from django.db.models import Q
from .models import Book, Biblio, Shelf, Floor
from .forms import BookForm, BiblioForm, ShelfForm, FllorForm

def index(request):
    return render(request, "books/index.html")


#書籍一覧
class BookListView(ListView):
    model = Book
    template_name = "books/book_list.html"
    context_object_name = "books"
    ordering = ["-created_at"]
    paginate_by = 10
#検索機能
    def get_queryset(self):
        query = self.request.GET.get("q")
        if query:
            return Book.objects.filter(
                Q(biblio__title__icontains=query) |
                Q(biblio__author__icontains=query)|
                Q(biblio__isbn__exact=query)
            )
        else:
            return Book.objects.all()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
# 検索条件に応じてタイトルを変更
        query = self.request.GET.get("q")
        if query:
            context["page_title"] = f"[{query}]の検索結果[{self.object_list.count()}件]"
        else:
            context["page_title"] = "蔵書一覧"
        
        return context



#詳細画面
class BookDetailView(DetailView):
    model = Book
    template_name = "books/book_detail.html"
    context_object_name = "book"

#登録インデックス
class ManageIndexView(TemplateView):
    template_name = "books/manage_index.html"

#蔵書登録
class BookCreateView(CreateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"
    success_url = reverse_lazy("books:manageindex")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "蔵書登録"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context
    
class BiblioCreateView(CreateView):
    model = Biblio
    form_class = BiblioForm
    template_name = "books/generic_form.html"
    success_url = reverse_lazy("books:manageindex")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "書誌情報登録"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context

class ShelfCreateView(CreateView):
    model = Shelf
    form_class = ShelfForm
    template_name = "books/generic_form.html"
    success_url = reverse_lazy("books:manageindex")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "本棚登録"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context
    

    

