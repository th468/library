from catalog.models import Category
from django import template
from django.urls import NoReverseMatch, Resolver404, resolve, reverse

register = template.Library()


@register.inclusion_tag("common/includes/_category_sidebar.html")
def get_category_list():
    """
    全カテゴリを取得し、サイドバー用のテンプレートに渡す。
    """
    categories = Category.objects.all().order_by("name")
    return {"categories": categories}


@register.inclusion_tag("common/includes/_search_bar.html", takes_context=True)
def global_search_bar(context):
    """
    サイト全体で共通利用する検索バーを表示するタグ。
    現在の検索キーワードを初期値として保持する。
    """
    request = context.get("request")
    q = request.GET.get("q", "") if request else ""
    return {"q": q}


@register.simple_tag(takes_context=True)
def active_link(context, url_name, css_class="active"):
    """
    現在のURLが指定された url_name と一致する場合、css_class を返す。
    ナビゲーションのハイライトに使用。
    """
    request = context.get("request")
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


@register.inclusion_tag("common/includes/_breadcrumbs.html", takes_context=True)
def render_breadcrumbs(context):
    """
    URL パスを解析してパンくずリストを自動生成する。
    ラベルが定義されている有効なViewのみをリストに含める（デッドリンク防止）。
    """
    request = context.get("request")
    if not request or request.path == "/":
        return {"links": []}

    path = request.path.strip("/")
    segments = path.split("/")
    breadcrumbs = []
    current_url = "/"

    # 表示を許可するURL名称と日本語ラベルのマッピング
    label_map = {
        "dashboard:index": "マイページ",
        "catalog:booklist": "蔵書をさがす",
        "catalog:manageindex": "管理業務",
        "catalog:bookdetail": "書籍詳細",
        "accounts:login": "ログイン",
        "accounts:regist": "新規登録",
        "accounts:profile_detail": "プロフィール",
        "accounts:profile_edit": "プロフィール編集",
        "accounts:password_change": "パスワード変更",
        "accounts:password_change_done": "パスワード変更完了",
    }

    for segment in segments:
        if not segment:
            continue

        current_url += f"{segment}/"

        try:
            # 現在の階層のURLがViewとして解決可能かチェック
            match = resolve(current_url)
            view_name = f"{match.app_name}:{match.url_name}" if match.app_name else match.url_name

            # 1. View クラスの breadcrumb_label を優先
            view_class = getattr(match.func, "view_class", None)
            label = getattr(view_class, "breadcrumb_label", None) if view_class else None

            # 2. 定義がなければ label_map から取得
            if not label:
                label = label_map.get(view_name)

            # ラベルが見つからない場合は、中間パス（ページがない）とみなしてスキップ
            if not label:
                continue

            breadcrumbs.append({"label": label, "url": current_url})

        except Resolver404:
            # 解決できないパス（中間パス等）は表示しない
            continue

    return {"links": breadcrumbs}


@register.simple_tag
def relative_url(value, field_name, urlencode=None):
    """
    現在のURLパラメータを維持したまま、特定のパラメータを書き換える。
    """
    url = f"?{field_name}={value}"
    if urlencode:
        querystring = urlencode.split("&")
        filtered_querystring = filter(lambda p: p.split("=")[0] != field_name, querystring)
        encoded_querystring = "&".join(filtered_querystring)
        if encoded_querystring:
            url = f"{url}&{encoded_querystring}"
    return url


@register.filter
def get_item(dictionary, key):
    """
    辞書から指定したキーで値を取得する。
    """
    if not dictionary:
        return None
    return dictionary.get(key)


# --- 状態判定フィルタ ---


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
