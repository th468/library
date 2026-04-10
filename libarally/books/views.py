from django.urls import reverse_lazy
from django.shortcuts import render,redirect
from django.views.generic import ListView,DetailView,TemplateView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin

from .models import Book, Biblio, Shelf, Floor
from .forms import BookForm, BiblioForm, ShelfForm, FllorForm

#region __継承元となる親クラス__

#一覧ビュー用の抽象クラス
class GenericListView(ListView):
    template_name = "books/generic_list.html"
    context_object_name = "object_list"
    paginate_by = 10

    #__継承先で定義する項目__   
    model = None                                                                                                        
    page_title = ""
    search_field = []
    headers = []
    url_header = None #もしくは以下３つの変数を定義

    detail_url = None
    edit_url = None
    delete_url = None

    #一覧テーブルに表示する項目を、各子クラスのメソッドにて、リスト形式で定義する。
    def get_row_values(self, obj):
        return []
    
    #__継承先で定義する項目、ここまで__

    #検索機能
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q")
        if query:
            search_query = Q()
            for field in self.search_field:
                search_query |= Q(**{f"{field}__icontains": query})
            return queryset.filter(search_query).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_field"] = self.search_field
        context["headers"] = self.headers
        context["search_placeholder"] = ",".join(self.search_field) +"で検索..."

        #url_header変数を使ってurlを生成
        header = self.url_header
        d_url = self.detail_url or (f"books:{header}_detail" if header else None)
        e_url = self.edit_url or (f"books:{header}_update" if header else None)
        dl_url = self.delete_url or (f"books:{header}_delete" if header else None)
        
        context["detail_url"] = d_url
        context["edit_url"] = e_url
        context["delete_url"] = dl_url

        # 検索条件に応じてタイトルを変更
        query = self.request.GET.get("q", "").strip()
        if query:
            context["page_title"] = f"[{query}]の検索結果[{self.object_list.count()}件]"
        else:
            context["page_title"] = self.page_title
        #オブジェクトのPKと要素を辞書としてまとめる
        rows = []
        for obj in context["object_list"]:
          rows.append({
              "id": obj.pk,
              "values": self.get_row_values(obj)
          })
        context["rows"] = rows

        return context
    
#詳細ビュー用の抽象クラス
class GenericDetailView(DetailView):
    template_name = "books/generic_detail.html"

    #__継承先で定義する項目__   
    model = None                                                                                                        
    page_title = None
    url_header = None #もしくは以下３つの変数を定義

    list_url = None
    edit_url = None
    delete_url = None

    #テーブルに表示する項目と項目名を、各子クラスのメソッドにて、タプルのリストの形式で定義する。
    def get_field_data(self, obj):
        return [("field.verbose_name", "field.value")]
    
    #__継承先で定義する項目、ここまで__

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        
        #url_header変数を使ってurlを生成
        header = self.url_header
        l_url = self.list_url or (f"books:{header}_list" if header else None)
        e_url = self.edit_url or (f"books:{header}_update" if header else None)
        d_url = self.delete_url or (f"books:{header}_delete" if header else None)
        context["list_url"] = l_url
        context["edit_url"] = e_url
        context["delete_url"] = d_url

        context["field_data"] = self.get_field_data(self.object)

        return context

#スタッフ権限管理用の抽象クラス
class StaffManagerMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        return self.request.user.is_staff
    class Meta:
        abstract = True

#endregion

#region __個別のビュー__


def index(request):
    return render(request, "books/index.html")

# region __蔵書情報関連ビュー__

# #書籍一覧
# class BookListView(ListView):
#     model = Book
#     template_name = "books/book_list.html"
#     context_object_name = "books"
#     ordering = ["-created_at"]
#     paginate_by = 10
# #検索機能
#     def get_queryset(self):
#         query = self.request.GET.get("q")
#         if query:
#             return Book.objects.filter(
#                 Q(biblio__title__icontains=query) |
#                 Q(biblio__author__icontains=query)|
#                 Q(biblio__isbn__exact=query)
#             )
#         else:
#             return Book.objects.all()
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
# # 検索条件に応じてタイトルを変更
#         query = self.request.GET.get("q")
#         if query:
#             context["page_title"] = f"[{query}]の検索結果[{self.object_list.count()}件]"
#         else:
#             context["page_title"] = "蔵書一覧"
        
#         return context
    

# #詳細画面
# class BookDetailView(DetailView):
#     model = Book
#     template_name = "books/book_detail.html"
#     context_object_name = "book"

#管理インデックス
class ManageIndexView(TemplateView):
    template_name = "books/manage_index.html"

# #蔵書情報登録
# class BookCreateView(StaffManagerMixin, CreateView):
#     model = Book
#     form_class = BookForm
#     template_name = "books/generic_form.html"
#     success_url = reverse_lazy("books:manageindex")
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["title"] = "蔵書登録"
#         context["cancel_url"] = reverse_lazy("books:manageindex")
#         return context

# #蔵書情報更新
# class BookUpdateView(StaffManagerMixin, UpdateView):
#     model = Book
#     form_class = BookForm
#     template_name = "books/generic_form.html"
#     success_url = reverse_lazy("books:manageindex")
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["title"] = "蔵書情報の編集"
#         context["cancel_url"] = reverse_lazy("books:manageindex")
#         return context

# #蔵書情報削除
# class BookDeleteView(StaffManagerMixin, DeleteView):
#     model = Book
#     template_name = "books/delete_form.html"
#     success_url = reverse_lazy("books:manageindex")
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["title"] = "蔵書情報の削除"
#         context["cancel_url"] = reverse_lazy("books:manageindex")
#         return context

# # endregion

# region __書誌情報関連ビュー__

#書誌情報一覧
class BiblioListView(GenericListView):
    model = Biblio                                                                                                        
    page_title = "書誌情報一覧"
    search_field = ["isbn", "title", "author"]
    headers = ["ISBN", "タイトル", "著者", "出版社"]
    url_header = "biblio"
    
    #一覧テーブルに表示する項目を、各子クラスのメソッドにて、リスト形式で定義する。
    def get_row_values(self, obj):
        return [obj.isbn, obj.title, obj.author, obj.publisher]


#書誌情報詳細
class BiblioDetailView(GenericDetailView):
    model = Biblio                                                                                               
    page_title = "書誌情報詳細"
    url_header = "biblio" 

    #テーブルに表示する項目と項目名を、各子クラスのメソッドにて、タプルのリストの形式で定義する。
    def get_field_data(self, obj):
        return [("ISBN", obj.isbn), ("タイトル", obj.title), 
                ("著者", obj.author), ("出版社", obj.publisher)
                ]
    

#書誌情報登録
class BiblioCreateView(StaffManagerMixin, CreateView):
    model = Biblio
    form_class = BiblioForm
    template_name = "books/generic_form.html"
    success_url = reverse_lazy("books:manageindex")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "書誌情報登録"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context
    


#書誌情報更新
class BiblioUpdateView(StaffManagerMixin, UpdateView):
    model = Biblio
    form_class = BiblioForm
    template_name = "books/generic_form.html"
    success_url = reverse_lazy("books:manageindex")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "書誌情報の編集"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context

#書誌情報削除
class BiblioDeleteView(StaffManagerMixin, DeleteView):
    model = Biblio
    template_name = "books/delete_form.html"
    success_url = reverse_lazy("books:manageindex")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "書誌情報の削除"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context

# endregion 書誌情報関連ビュー

# region __本棚関連ビュー__

#本棚一覧
class ShelfListView(GenericListView):
    model = Shelf
    page_title = "本棚一覧"
    search_field = ["name"]
    headers = ["本棚名", "階"]
    url_header = "shelf"
    
    #一覧テーブルに表示する項目を、各子クラスのメソッドにて、リスト形式で定義する。
    def get_row_values(self, obj):
        return [obj.name, obj.floor.name]
    
# endregion 本棚関連ビュー

# region __階情報関連ビュー__

#階情報一覧
class FloorListView(GenericListView):
    model = Floor                                                                                                     
    page_title = "フロア一覧"
    search_field = ["name"]
    headers = ["フロア名"]
    url_header = "floor"
    
    #一覧テーブルに表示する項目を、各子クラスのメソッドにて、リスト形式で定義する。
    def get_row_values(self, obj):
        return [obj.name]


#階情報詳細
class FloorDetailView(GenericDetailView):
    model = Floor                                                                                               
    page_title = "フロア情報詳細"
    url_header = "floor" 

    #テーブルに表示する項目と項目名を、各子クラスのメソッドにて、タプルのリストの形式で定義する。
    def get_field_data(self, obj):
        return [("ISBN", obj.isbn), ("タイトル", obj.title), 
                ("著者", obj.author), ("出版社", obj.publisher)
                ]
    

#書誌情報登録
class BiblioCreateView(StaffManagerMixin, CreateView):
    model = Biblio
    form_class = BiblioForm
    template_name = "books/generic_form.html"
    success_url = reverse_lazy("books:manageindex")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "書誌情報登録"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context
    


#書誌情報更新
class BiblioUpdateView(StaffManagerMixin, UpdateView):
    model = Biblio
    form_class = BiblioForm
    template_name = "books/generic_form.html"
    success_url = reverse_lazy("books:manageindex")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "書誌情報の編集"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context

#書誌情報削除
class BiblioDeleteView(StaffManagerMixin, DeleteView):
    model = Biblio
    template_name = "books/delete_form.html"
    success_url = reverse_lazy("books:manageindex")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "書誌情報の削除"
        context["cancel_url"] = reverse_lazy("books:manageindex")
        return context

# endregion 書誌情報関連ビュー
