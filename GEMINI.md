# Project Instructions: Library

## 1. プロジェクト目的と背景
- **目的:** 就職活動用ポートフォリオ。架空会社からの依頼に基づく分散型図書館アプリのプロトタイプ。
- **課題:** 20フロアに分散した1.5万冊の蔵書を、物理移動なしに「仮想本棚」で一括管理・貸出可能にする。
- **UX制約:** 持ち出し防止とデータ整合性のため、**場所情報は貸出/予約確定時のみ表示**する設計を厳守する。

## 2. ディレクトリ構造の役割
- `library/`: Djangoプロジェクトルート
  - `core/`: 抽象基盤（BaseModel, Mixins, Tags）。全アプリの共通規約。
  - `accounts/`: ユーザー認証、部署管理、権限。
  - `books/`: 静的データ管理（書誌・蔵書・保管場所・お気に入り）。
  - `transactions/`: 動的ライフサイクル（貸出・予約ロジック）。※最重要
  - `dashboard/`: 統合UI。複数アプリの情報を横断的に表示するポータル画面。

## 3. 技術スタック
- **Framework:** Django 6.0.2 / Python 3.14
- **Tools:** django-widget-tweaks, Factory Boy, Faker
- **Quality:** Ruff (Lint/Format), mypy (Type Check)
- **Database:** SQLite3

## 4. 開発・コーディング規約
### モデルとロジック
- **BaseModel継承:** 全モデルで `core.models.BaseModel` を継承し、`is_active` による論理削除を標準とする。
- **ロジック配置:** 1.Model (Fat Model) > 2.Form > 3.Service。Viewにはビジネスロジックを書かない (Thin View)。
- **View:** クラスベースビュー (CBV) を優先。
- **命名:** PEP8準拠（Class: PascalCase, Var/Func: snake_case）。

### テスト
- **Factory活用:** `factories.py` を必須とし、`BaseModelTestMixin` で論理削除と `__str__` を厳密に検証する。
- **網羅性:** 正常系・異常系に加え、境界値（最大文字数、日付の前後関係）を必ず含めること。

### テンプレート
- `common/base.html` を継承。UI部品は `common/includes/` で共通化し、DRYを徹底する。

## 5. 運用・コミュニケーションルール
- **TODO管理:** 実装時に発見した将来的な改善点や技術的負債は、必ず `docs/TODO.md` に記録すること。
- **変更提案:** 修正前に「修正箇所一覧」と「理由 (Rationale)」を提示すること。
- **構造優先:** 局所的な修正より先に、設計やデータ構造の問題を確認・報告すること。
- **透明性:** コマンドは `&&` で連結せず、一つずつ実行・確認する。
- **効率的更新:** `replace` ツールを優先し、ピンポイントで正確に修正する（省略記号 `...` は使用不可）。

## 6. 主要コマンド
- テスト: `python library/manage.py test library`
- 品質チェック: `ruff check .` / `mypy .`
- DB: `python library/manage.py makemigrations` / `migrate`
