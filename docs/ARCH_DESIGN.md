# Architectural Design & Rationale

This document describes the architectural decisions and technical challenges addressed in the Library project.

## 1. User Library Status Optimization (Hierarchical Mixins)

### 1.1. The Challenge: N+1 Query Problem
In book listing views (search results, category views), displaying the user's status for each book (e.g., "Is it favorited?", "Is it currently lent to me?") caused a significant performance bottleneck.
- **Root Cause:** Standard template filters or model methods performed a database query for *each* item in the loop, resulting in $N$ additional queries where $N$ is the number of books displayed.

### 1.2. The Solution: Hierarchical Context Mixins
We implemented a set of reusable Mixins in `core/views/mixins.py` to pre-fetch status data efficiently.

- **Granularity (Single Responsibility):**
    - `FavoriteContextMixin`: Fetches favorite book IDs.
    - `LendingContextMixin`: Fetches currently lent book IDs.
    - `ReservationContextMixin`: Fetches currently reserved book IDs.
- **Facade Pattern:** `LibStatusMixin` inherits all three, providing a single point of integration for views that require full status awareness.

### 1.3. Technical Optimizations
- **Memory Efficiency:** Used `.values_list('biblio_id', flat=True)` to fetch only the necessary primary keys, avoiding the overhead of instantiating full Django Model objects.
- **Lookup Performance:** Converted query results into Python `set` objects. This ensures that template-side checks (`{% if id in ids %}`) run in $O(1)$ constant time instead of $O(n)$ linear time.
- **Dependency Management:** Used local imports within methods to prevent circular dependency issues between the `core`, `catalog`, and `transactions` apps.

---

## 1. ユーザーライブラリステータスの最適化（階層型 Mixin）

<aside>
### 1.1. 課題：N+1 クエリ問題
書籍一覧表示（検索結果やカテゴリ別リスト）において、各書籍に対するユーザー固有の状態（お気に入り済みか、貸出中か等）を確認する処理が、深刻なパフォーマンスのボトルネックとなっていました。
- **根本原因:** 標準的なテンプレートフィルタやモデルメソッドがループ内の各アイテムに対してデータベースクエリを実行するため、表示件数 $N$ に対して $N$ 回の追加クエリが発生していました。

### 1.2. 解決策：階層型コンテキスト Mixin
`core/views/mixins.py` に、状態データを効率的に事前取得するための再利用可能な Mixin 群を実装しました。

- **粒度の細分化（単一責任の原則）:**
    - `FavoriteContextMixin`: お気に入り書誌IDを取得。
    - `LendingContextMixin`: 貸出中書誌IDを取得。
    - `ReservationContextMixin`: 予約中書誌IDを取得。
- **ファサードパターン:** `LibStatusMixin` が上記3つを継承し、全ステータスを必要とするビューに対して単一の統合ポイントを提供します。

### 1.3. 技術的な最適化
- **メモリ効率:** `.values_list('biblio_id', flat=True)` を使用して必要な主キーのみを取得し、Django モデルオブジェクト全体のインスタンス化に伴うオーバーヘッドを回避しました。
- **検索パフォーマンス:** クエリ結果を Python の `set`（集合型）に変換しました。これにより、テンプレート側での判定（`{% if id in ids %}`）が $O(n)$ の線形時間ではなく $O(1)$ の定数時間で実行されることを保証します。
- **依存関係の管理:** `core`、`catalog`、`transactions` アプリ間の循環参照を防ぐため、メソッド内でのローカルインポートを採用しました。
</aside>
