from django import template
from django.urls import reverse, NoReverseMatch
from catalog.models import Category

register = template.Library()

@register.inclusion_tag('common/includes/_category_sidebar.html')
def get_category_list():
    """
    全カテゴリを取得し、サイドバー用のテンプレートに渡す。
    """
    categories = Category.objects.all().order_by('name')
    return {'categories': categories}

@register.inclusion_tag('common/includes/_search_bar.html', takes_context=True)
def global_search_bar(context):
    """
    サイト全体で共通利用する検索バーを表示するタグ。
    現在の検索キーワードを初期値として保持する。
    """
    request = context.get('request')
    q = request.GET.get('q', '') if request else ""
    return {'q': q}

@register.simple_tag(takes_context=True)
def active_link(context, url_name, css_class='active'):
    """
    現在のURLが指定された url_name と一致する場合、css_class を返す。
    ナビゲーションのハイライトに使用。
    """
    request = context.get('request')
    if not request:
        return ""
    
    try:
        # url_name から実際のパスを逆引き
        target_url = reverse(url_name)
        # 現在のパスがターゲットURLで始まっているか判定
        # (前方一致にすることで、詳細画面等でも親メニューをハイライトできる)
        if request.path.startswith(target_url):
            return css_class
    except NoReverseMatch:
        pass
    
    return ""

@register.inclusion_tag('common/includes/_breadcrumbs.html', takes_context=True)
def render_breadcrumbs(context):
    """
    URL パスを解析してパンくずリストを自動生成する。
    """
    request = context.get('request')
    if not request or request.path == '/':
        return {'links': []}

    path = request.path.strip('/')
    segments = path.split('/')
    
    # URL セグメントと日本語ラベルのマッピング
    label_map = {
        'catalog': '蔵書をさがす',
        'list': '検索結果',
        'detail': '書籍詳細',
        'dashboard': 'マイページ',
        'accounts': 'ユーザー',
        'login': 'ログイン',
        'regist': '新規登録',
        'manage': '管理メニュー',
        'info': 'ユーザー情報',
    }

    breadcrumbs = []
    current_url = '/'
    
    for i, segment in enumerate(segments):
        if not segment:
            continue
            
        current_url += f"{segment}/"
        
        # ID（数字）の場合は「詳細」などのラベルにする
        if segment.isdigit():
            # 1つ前のセグメントを見てラベルを調整
            prev = segments[i-1] if i > 0 else ""
            if prev == 'detail':
                label = '詳細'
            elif prev == 'update':
                label = '編集'
            else:
                label = f'#{segment}'
        else:
            label = label_map.get(segment, segment.capitalize())

        breadcrumbs.append({'label': label, 'url': current_url})

    return {'links': breadcrumbs}


@register.simple_tag
def relative_url(value, field_name, urlencode=None):
    """
    現在のURLパラメータを維持したまま、特定のパラメータを書き換える。
    """
    url = f'?{field_name}={value}'
    if urlencode:
        querystring = urlencode.split('&')
        filtered_querystring = filter(lambda p: p.split('=')[0] != field_name, querystring)
        encoded_querystring = '&'.join(filtered_querystring)
        if encoded_querystring:
            url = f'{url}&{encoded_querystring}'
    return url


# --- 状態判定フィルタ ---

@register.filter
def is_lent_by(obj, user):
    """
    ユーザーが対象を現在借りているか判定。
    obj が Biblio の場合は「そのタイトルのいずれか」を、
    obj が Book の場合は「その個体」を借りているか判定。
    """
    if not user or not user.is_authenticated:
        return False
    from catalog.models import Biblio, Book
    from transactions.models import Lending

    if isinstance(obj, Biblio):
        return Lending.objects.ongoing().filter(book__biblio=obj, user=user).exists()
    elif isinstance(obj, Book):
        return Lending.objects.ongoing().filter(book=obj, user=user).exists()
    return False


@register.filter
def is_reserved_by(biblio, user):
    """ユーザーがその書誌を現在予約しているか判定"""
    if not user or not user.is_authenticated:
        return False
    from transactions.models import Reservation
    return Reservation.objects.ongoing().filter(biblio=biblio, user=user).exists()


@register.filter
def is_lent_by_others(biblio, user):
    """自分以外のユーザーがその書誌（のいずれかの在庫）を現在借りているか判定"""
    if not user or not user.is_authenticated:
        return False
    from transactions.models import Lending
    return Lending.objects.ongoing().filter(book__biblio=biblio).exclude(user=user).exists()


@register.filter
def user_lending(biblio, user):
    """ユーザーがその書誌を借りている場合、その Lending オブジェクトを返す"""
    if not user or not user.is_authenticated:
        return None
    from transactions.models import Lending
    return Lending.objects.ongoing().filter(book__biblio=biblio, user=user).first()


@register.filter
def is_favorited_by(biblio, user):
    """ユーザーがその書誌をお気に入り登録しているか判定"""
    if not user or not user.is_authenticated:
        return False
    from catalog.models import Favorite
    return Favorite.objects.filter(biblio=biblio, user=user).exists()
