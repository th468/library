import random
from datetime import timedelta

from accounts.factories import DepartmentFactory, UserFactory
from accounts.models import User
from catalog.factories import (
    BiblioFactory,
    BookFactory,
    FloorFactory,
    ShelfFactory,
)
from catalog.models import Biblio, Book, Category, Favorite, Floor, Shelf
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone
from transactions.models import Lending, Reservation


class Command(BaseCommand):
    help = "動作確認・デモ表示用のデータベースシードデータを生成します（既存データは一掃されます）。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="実行前の警告プロンプトと確認メッセージを表示せず、強制的に実行します。",
        )

    def handle(self, *args, **options):
        # 1. 安全装置: DEBUG=False の場合は実行を拒否
        if not settings.DEBUG:
            raise CommandError(
                "本番環境（DEBUG=False）でシードデータコマンドを実行することはできません。 "
                "データ損失を防ぐため、実行をキャンセルしました。"
            )

        # 2. 安全装置: 対話型プロンプトによる実行確認
        if not options["no_input"]:
            self.stdout.write(
                self.style.WARNING(
                    "【警告】このコマンドを実行すると、データベース内の既存のすべてのデータが物理削除（一掃）されます。"
                )
            )
            confirm = input("本当に実行してよろしいですか？ [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.NOTICE("実行をキャンセルしました。"))
                return

        self.stdout.write("=== 全データを一掃し、クリーンな再投入を開始します ===")

        # 3. データの物理削除
        self._clear_database()

        # 4. 基礎データの作成
        admin, depts, categories, floors, shelves, users = self._create_base_data()

        # 5. 書籍の作成
        self._create_books_and_biblios(categories, shelves)

        # 6. トランザクションデータの作成 (お気に入り、貸出、予約)
        self._create_transaction_data(admin, users)

        # 7. 統計レポート
        self._print_stats()

    def _clear_database(self):
        # 外部キー制約を一時的に無視して物理削除 (SQLite用)
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys = OFF;")

                self.stdout.write("既存データを一括削除中...")
                # BaseModel の論理削除を回避するため、all_objects.hard_delete() を使用
                Lending.all_objects.hard_delete()
                Reservation.all_objects.hard_delete()
                Book.all_objects.hard_delete()
                Biblio.all_objects.hard_delete()
                Category.all_objects.hard_delete()
                Shelf.all_objects.hard_delete()
                Floor.all_objects.hard_delete()
                # 管理者以外のユーザーを物理削除
                User.objects.exclude(email="admin@example.com").delete()

                cursor.execute("PRAGMA foreign_keys = ON;")

    def _create_base_data(self):
        self.stdout.write("基礎データを再構築中...")

        # 管理者ユーザー
        admin, created = User.objects.get_or_create(
            email="admin@example.com",
            defaults={
                "em_num": "ADMIN001",
                "is_staff": True,
                "is_superuser": True,
                "name": "管理者 太郎",
                "lending_limit": 10,
            },
        )
        if created:
            admin.set_password("password123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("  - 管理者ユーザーを作成しました: admin@example.com / password123"))
        elif admin.lending_limit != 10:
            admin.lending_limit = 10
            admin.save(update_fields=["lending_limit"])

        # 部署
        depts = DepartmentFactory.create_batch(5)
        self.stdout.write(f"  - 部署を {len(depts)} 件作成しました。")

        # カテゴリ
        category_names = ["IT・技術書", "ビジネス・経済", "デザイン・アート", "小説・文芸", "雑誌"]
        categories = [Category.objects.create(name=name) for name in category_names]
        self.stdout.write(f"  - カテゴリを {len(categories)} 件作成しました。")

        # フロアと棚
        floors = FloorFactory.create_batch(3)
        shelves = []
        for floor in floors:
            shelves.extend(ShelfFactory.create_batch(3, floor=floor))
        self.stdout.write(f"  - フロア {len(floors)} 件、棚 {len(shelves)} 件を作成しました。")

        # 一般ユーザー
        users = UserFactory.create_batch(10, department=random.choice(depts))
        self.stdout.write(f"  - 一般ユーザーを {len(users)} 件作成しました。")

        return admin, depts, categories, floors, shelves, users

    def _create_books_and_biblios(self, categories, shelves):
        self.stdout.write("書籍データを生成中...")
        for _ in range(50):
            biblio = BiblioFactory()
            # カテゴリをランダムに1〜2個紐付け
            biblio.categories.set(random.sample(categories, random.randint(1, 2)))

            # 各書誌に対して1〜3冊の蔵書(Book)を作成
            for _ in range(random.randint(1, 3)):
                BookFactory(biblio=biblio, shelf=random.choice(shelves))

        self.stdout.write(f"  - 書誌 {Biblio.objects.count()} 件、蔵書 {Book.objects.count()} 件を作成しました。")

    def _create_transaction_data(self, admin, users):
        # お気に入りデータの作成
        self._create_favorites(admin)

        # 返記済み履歴（過去の貸出）データの作成
        self._create_returned_history(admin, users)

        # 現在進行中の貸出（通常・延滞）データの作成
        self._create_active_lendings(admin, users)

        # 予約データの作成
        self._create_reservations(admin, users)

    def _create_favorites(self, admin):
        admin_favorites_count = 0
        all_biblios = list(Biblio.objects.all())
        random.shuffle(all_biblios)
        for biblio in all_biblios:
            if admin_favorites_count >= 5:
                break
            Favorite.objects.get_or_create(user=admin, biblio=biblio)
            admin_favorites_count += 1
        self.stdout.write(f"  - 管理者お気に入りデータを {admin_favorites_count} 件作成しました。")

    def _create_returned_history(self, admin, users):
        from django.core.exceptions import ValidationError

        self.stdout.write("過去の返却済み履歴データを生成中...")
        available_books = list(Book.objects.filter(status=Book.Status.AVAILABLE))
        active_users = list(users)

        # 管理者用 (10件)
        admin_returned_count = 0
        for _ in range(10):
            if not available_books:
                break
            book = available_books.pop()
            try:
                lending = Lending.objects.lend(book, admin)
                Lending.objects.collect(lending, admin)
                lending.created_at = timezone.now() - timedelta(days=20)
                lending.due_date = (timezone.now() - timedelta(days=20)).date() + timedelta(days=14)
                lending.return_date = timezone.now().date() - timedelta(days=6)
                lending.save(update_fields=["created_at", "due_date", "return_date"])
                admin_returned_count += 1
            except ValidationError as e:
                self.stdout.write(self.style.WARNING(f"  - 管理者返却履歴作成スキップ: {e}"))
        self.stdout.write(f"  - 管理者返却済み履歴データを {admin_returned_count} 件作成しました。")

        # 一般ユーザー用 (10件)
        general_returned_count = 0
        for _ in range(10):
            if not available_books or not active_users:
                break
            book = available_books.pop()
            user = random.choice(active_users)
            try:
                lending = Lending.objects.lend(book, user)
                Lending.objects.collect(lending, user)
                lending.created_at = timezone.now() - timedelta(days=10)
                lending.due_date = (timezone.now() - timedelta(days=10)).date() + timedelta(days=14)
                lending.return_date = timezone.now().date() - timedelta(days=3)
                lending.save(update_fields=["created_at", "due_date", "return_date"])
                general_returned_count += 1
            except ValidationError as e:
                self.stdout.write(self.style.WARNING(f"  - 一般返却履歴作成スキップ: {e}"))
        self.stdout.write(f"  - 一般返却済み履歴データを {general_returned_count} 件作成しました。")

    def _create_active_lendings(self, admin, users):
        self.stdout.write("現在進行中の貸出データを生成中...")
        available_books = list(Book.objects.filter(status=Book.Status.AVAILABLE))
        active_users = list(users)

        self._create_admin_active_lendings(admin, available_books)
        self._create_general_active_lendings(active_users, available_books)

    def _create_admin_active_lendings(self, admin, available_books):
        from django.core.exceptions import ValidationError

        admin_active_lendings = []
        for _ in range(7):
            if not available_books:
                break
            book = available_books.pop()
            try:
                lending = Lending.objects.lend(book, admin)
                admin_active_lendings.append(lending)
            except ValidationError as e:
                self.stdout.write(self.style.WARNING(f"  - 管理者貸出作成スキップ: {e}"))

        # そのうちの2件を延滞化
        admin_overdue_count = 0
        for i, lending in enumerate(admin_active_lendings):
            if i >= 2:
                break
            lending.due_date = timezone.now().date() - timedelta(days=5)
            lending.save(update_fields=["due_date"])
            admin_overdue_count += 1
        self.stdout.write(
            f"  - 管理者通常貸出中データを {len(admin_active_lendings) - admin_overdue_count} 件、"
            f"延滞貸出データを {admin_overdue_count} 件作成しました。"
        )

    def _create_general_active_lendings(self, active_users, available_books):
        from django.core.exceptions import ValidationError

        general_active_lendings = []
        for _ in range(13):
            if not available_books or not active_users:
                break
            book = available_books.pop()
            user = random.choice(active_users)
            try:
                lending = Lending.objects.lend(book, user)
                general_active_lendings.append(lending)
            except ValidationError as e:
                self.stdout.write(self.style.WARNING(f"  - 一般貸出作成スキップ: {e}"))

        # そのうちの3件を延滞化
        general_overdue_count = 0
        for i, lending in enumerate(general_active_lendings):
            if i >= 3:
                break
            lending.due_date = timezone.now().date() - timedelta(days=7)
            lending.save(update_fields=["due_date"])
            general_overdue_count += 1
        self.stdout.write(
            f"  - 一般通常貸出中データを {len(general_active_lendings) - general_overdue_count} 件、"
            f"延滞貸出データを {general_overdue_count} 件作成しました。"
        )

    def _create_reservations(self, admin, users):
        self.stdout.write("予約データを生成中...")
        active_users = list(users)

        self._create_admin_reservations(admin)
        self._create_general_reservations(active_users)

    def _create_admin_reservations(self, admin):
        from django.core.exceptions import ValidationError

        # 管理者が現在借りている書誌IDを取得（予約重複エラー回避のため）
        admin_borrowed_biblio_ids = list(
            Lending.objects.ongoing().filter(user=admin).values_list("book__biblio_id", flat=True)
        )

        admin_ready_res_count = 0
        admin_waiting_res_count = 0

        # 全書誌をシャッフルしてループ
        all_biblios = list(Biblio.objects.all())
        random.shuffle(all_biblios)

        # READY用書誌とWAITING用書誌の選定
        for biblio in all_biblios:
            if admin_ready_res_count >= 3 and admin_waiting_res_count >= 2:
                break

            # すでに管理者が借りている、または予約済みのものはスキップ
            if biblio.id in admin_borrowed_biblio_ids:
                continue
            if Reservation.objects.ongoing().filter(user=admin, biblio=biblio).exists():
                continue

            books = biblio.books.all()
            if not books.exists():
                continue

            # 在庫（AVAILABLE）があるかどうか
            has_available = books.filter(status=Book.Status.AVAILABLE).exists()

            if has_available and admin_ready_res_count < 3:
                # 在庫があるので、予約を作成すると確実に READY に引き当てられる
                try:
                    Reservation.objects.create_reservation(admin, biblio)
                    admin_ready_res_count += 1
                except ValidationError as e:
                    self.stdout.write(self.style.WARNING(f"  - 管理者準備完了予約作成スキップ: {e}"))
            elif not has_available and admin_waiting_res_count < 2:
                # 在庫がないので、予約を作成すると確実に WAITING（入荷待ち）になる
                try:
                    Reservation.objects.create_reservation(admin, biblio)
                    admin_waiting_res_count += 1
                except ValidationError as e:
                    self.stdout.write(self.style.WARNING(f"  - 管理者入荷待ち予約作成スキップ: {e}"))

        self.stdout.write(
            f"  - 管理者準備完了予約（取置中）データを {admin_ready_res_count} 件、"
            f"入荷待ち予約データを {admin_waiting_res_count} 件作成しました。"
        )

    def _create_general_reservations(self, active_users):
        general_ready_res_count = 0
        general_waiting_res_count = 0
        general_canceled_res_count = 0

        all_biblios = list(Biblio.objects.all())
        random.shuffle(all_biblios)

        for biblio in all_biblios:
            if general_ready_res_count >= 5 and general_waiting_res_count >= 5 and general_canceled_res_count >= 2:
                break

            # ランダムにユーザーを1人選定
            user = random.choice(active_users)
            res_type = self._try_create_general_reservation(
                user, biblio, general_ready_res_count, general_waiting_res_count, general_canceled_res_count
            )

            if res_type == "ready":
                general_ready_res_count += 1
            elif res_type == "waiting":
                general_waiting_res_count += 1
            elif res_type == "canceled":
                general_canceled_res_count += 1

        self.stdout.write(
            f"  - 一般準備完了予約（取置中）データを {general_ready_res_count} 件、"
            f"入荷待ち予約データを {general_waiting_res_count} 件、"
            f"キャンセル済み予約データを {general_canceled_res_count} 件作成しました。"
        )

    def _try_create_general_reservation(self, user, biblio, ready_count, waiting_count, canceled_count):
        from django.core.exceptions import ValidationError

        # すでに該当ユーザーが借りている、または予約済みの場合はスキップ
        if Lending.objects.ongoing().filter(user=user, book__biblio=biblio).exists():
            return None
        if Reservation.objects.ongoing().filter(user=user, biblio=biblio).exists():
            return None

        books = biblio.books.all()
        if not books.exists():
            return None

        has_available = books.filter(status=Book.Status.AVAILABLE).exists()

        if has_available and ready_count < 5:
            try:
                Reservation.objects.create_reservation(user, biblio)
                return "ready"
            except ValidationError as e:
                self.stdout.write(self.style.WARNING(f"  - 一般準備完了予約作成スキップ: {e}"))
        elif not has_available and waiting_count < 5:
            try:
                Reservation.objects.create_reservation(user, biblio)
                return "waiting"
            except ValidationError as e:
                self.stdout.write(self.style.WARNING(f"  - 一般入荷待ち予約作成スキップ: {e}"))
        elif canceled_count < 2:
            # キャンセル用データ（予約してから即時キャンセル）
            try:
                res = Reservation.objects.create_reservation(user, biblio)
                Reservation.objects.cancel_reservation(res, remark="ユーザー都合によるキャンセル（デモ）")
                return "canceled"
            except ValidationError as e:
                self.stdout.write(self.style.WARNING(f"  - 一般キャンセル予約作成スキップ: {e}"))
        return None

    def _print_stats(self):
        # 統計レポート
        self.stdout.write(self.style.SUCCESS("\n=== 完了しました！ ==="))
        self.stdout.write(f"  - 書誌 (Biblio) 数: {Biblio.objects.count()}")
        self.stdout.write(f"  - 蔵書 (Book) 数  : {Book.objects.count()}")
        self.stdout.write(f"    * 在庫あり (AVAILABLE): {Book.objects.filter(status=Book.Status.AVAILABLE).count()}")
        self.stdout.write(f"    * 貸出中   (LENT)     : {Book.objects.filter(status=Book.Status.LENT).count()}")
        self.stdout.write(f"    * 予約中   (RESERVED) : {Book.objects.filter(status=Book.Status.RESERVED).count()}")
        self.stdout.write(f"  - ユーザー数       : {User.objects.count()}")
        self.stdout.write(f"  - 貸出レコード数   : {Lending.objects.count()}")
        self.stdout.write(f"  - 予約レコード数   : {Reservation.objects.count()}")
        self.stdout.write(f"  - お気に入り数     : {Favorite.objects.count()}")
        self.stdout.write("  - ログイン情報: admin@example.com / password123")
