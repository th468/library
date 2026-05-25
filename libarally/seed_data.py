import os
import django

# Djangoの設定をロード
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'libarally.settings')
django.setup()

from django.db import connection
from books.models import Book, Biblio, Category, Floor, Shelf
from transactions.models import Lending, Reservation
from accounts.models import User

def clean_and_seed():
    print("=== 全データを一掃し、クリーンな再投入を開始します ===")

    # 1. 外部キー制約を一時的に無視して全削除 (SQLite用)
    with connection.cursor() as cursor:
        cursor.execute('PRAGMA foreign_keys = OFF;')
        
        print("既存データを一括削除中...")
        Lending.objects.all().delete()
        Reservation.objects.all().delete()
        Book.objects.all().delete()
        Biblio.objects.all().delete()
        Category.objects.all().delete()
        Shelf.objects.all().delete()
        Floor.objects.all().delete()
        User.objects.exclude(email="admin@example.com").delete()
        
        cursor.execute('PRAGMA foreign_keys = ON;')

    # 2. 基礎データの作成
    print("基礎データを再構築中...")
    admin, created = User.objects.get_or_create(
        email="admin@example.com",
        defaults={'em_num': 'ADMIN001', 'is_staff': True, 'is_superuser': True, 'name': '管理者 太郎'}
    )
    if created:
        admin.set_password("password123")
        admin.save()
    
    cat_it = Category.objects.create(name="IT・技術書")
    cat_novel = Category.objects.create(name="小説")
    floor_1 = Floor.objects.create(name="1F")
    shelf_main = Shelf.objects.create(name="メイン本棚", floor=floor_1, description="1F 受付横の大きな本棚です。")

    # 3. 本の作成 (確実に整合性を保ちながら作成)
    print("20冊の本を生成中...")
    for i in range(20):
        isbn = f"978-4-9999{i:04d}"
        biblio = Biblio.objects.create(
            isbn=isbn,
            title=f"Djangoプロフェッショナル開発ガイド Vol.{i+1}",
            author="Gemini メンター",
            publisher="Libarally Press",
            description=f"これは {i+1} 冊目のサンプル書籍です。15,000冊を支えるシステムの検証用データです。"
        )
        # カテゴリの紐付け
        biblio.categories.add(cat_it if i % 2 == 0 else cat_novel)
        
        # 実体(Book)の作成
        # models.py の save() 内の自動採番ロジックを確実に走らせる
        Book.objects.create(
            biblio=biblio,
            shelf=shelf_main,
            status=1 # AVAILABLE
        )

    print(f"\n=== 完了しました！ ===")
    print(f"Books: {Book.objects.count()}, Biblios: {Biblio.objects.count()}")
    print(f"ログイン: admin@example.com / password123")

if __name__ == "__main__":
    clean_and_seed()
