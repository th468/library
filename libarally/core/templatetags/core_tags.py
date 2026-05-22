from django import template
from books.models import Category

register = template.Library()

@register.inclusion_tag('common/includes/_category_sidebar.html')
def get_category_list():
    """
    全カテゴリを取得し、サイドバー用のテンプレートに渡す。
    Inclusion Tag を使うことで、View側での処理なしにサイドバーを表示できる。
    """
    # 各カテゴリを取得（将来的に件数集計などもここで行える）
    categories = Category.objects.all().order_by('name')
    return {'categories': categories}

@register.simple_tag
def relative_url(value, field_name, urlencode=None):
    """
    現在のURLパラメータを維持したまま、特定のパラメータ（pageやsortなど）だけを書き換える。
    検索条件を保持したままページ移動するために必須。
    """
    url = f'?{field_name}={value}'
    if urlencode:
        querystring = urlencode.split('&')
        # すでに存在する同じパラメータを一旦除外して再構築
        filtered_querystring = filter(lambda p: p.split('=')[0] != field_name, querystring)
        encoded_querystring = '&'.join(filtered_querystring)
        if encoded_querystring:
            url = f'{url}&{encoded_querystring}'
    return url
