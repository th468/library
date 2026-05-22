import os
import django
import random

# Djangoの設定をロード
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'libarally.settings')
django.setup()

from books.models import Book, Biblio, Category, Floor, Shelf
from transactions.models import Lending, Reservation
from accounts.models import User
from books.factories import BiblioFactory, BookFactory

def seed():
    print("=== 堅牢なデータ投入を開始します ===")

    # 1. 管理者
    admin, _ = User.objects.get_or_create(
        email="admin@example.com",
        defaults={'em_num': 'ADMIN001', 'is_staff': True, 'is_superuser': True, 'name': '管理者 太郎'}
    )
    admin.set_password("password123")
    admin.save()

    # 2. カテゴリ
    category_names = ["プログラミング", "デザイン", "マネジメント", "経済", "雑誌", "自己啓発", "小説"]
    categories = []
    for name in category_names:
        cat, _ = Category.objects.get_or_create(name=name)
        categories.append(cat)

    # 3. フロアと棚
    floor, _ = Floor.objects.get_or_create(name="1F")
    shelf, _ = Shelf.objects.get_or_create(name="メイン棚", floor=floor)

    # 4. 書誌と蔵書の作成 (足りない分だけ作成)
    current_count = Biblio.objects.count()
    target_count = 20
    if current_count < target_count:
        created_count = 0
        for i in range(target_count + 10): # 予備を含めて回す
            if created_count >= target_count:
                break
            try:
                # 重複エラーを避けるため、一意な要素を手動で補強
                biblio = BiblioFactory()
                biblio.categories.add(random.choice(categories))
                BookFactory(biblio=biblio, shelf=shelf)
                created_count += 1
            except Exception:
                # ISBN衝突などは無視して次へ
                continue
        print(f"書誌データを補充しました。現在: {Biblio.objects.count()}件")
    else:
        print(f"十分なデータがあります ({current_count}件)。")

    # 5. 貸出データ (管理者用)
    if not admin.lending_set.exists():
        book = Book.objects.filter(status=1).first() # AVAILABLE
        if book:
            try:
                Lending.objects.lend(book, admin)
                print("貸出データを作成しました。")
            except Exception as e:
                print(f"貸出データの作成に失敗しました: {e}")

    print("\n=== 完了 ===")
    print("ログインURL: /accounts/login/")
    print("ログイン: admin@example.com / password123")

if __name__ == "__main__":
    seed()
