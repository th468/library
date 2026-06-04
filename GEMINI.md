# Project Instructions: Library

## 1. Project Overview & Objectives
- **Goal:** Career portfolio. Prototype of a distributed library application for a hypothetical company.
- **Challenge:** Manage 15,000 volumes across 20 floors in a "virtual bookshelf" without physical relocation.
- **UX Constraint:** Location details **MUST ONLY** be revealed after checkout or reservation confirmation to prevent unrecorded removal and ensure data integrity.

## 2. Directory Architecture
- `library/`: Django project root.
  - `core/`: Abstract foundation (BaseModel, Mixins, Tags). Global conventions for all apps.
  - `accounts/`: Authentication, department management, and permissions.
  - `catalog/`: Static data (Biblios, Books, Locations, Favorites).
  - `transactions/`: Dynamic lifecycle (Lending and Reservation logic). **Mission-critical.**
  - `dashboard/`: Integrated portal UI. Cross-app data visualization.

## 3. Tech Stack
- **Framework:** Django 6.0.2 / Python 3.14
- **Tools:** django-widget-tweaks, Factory Boy, Faker
- **Quality:** Ruff (Lint/Format), mypy (Type Check)
- **Database:** SQLite3

## 4. Engineering Standards
### Models & Logic
- **BaseModel Inheritance:** All models **MUST** inherit from `core.models.BaseModel` for standardized logical deletion via `is_active`.
- **Logic Placement:** Prioritize 1. Model (Fat Model) > 2. Form > 3. Service. **DO NOT** implement business logic in Views (Thin View).
- **Views:** Prioritize Class-Based Views (CBV).
- **Naming:** STRICT PEP8 compliance (Class: PascalCase, Var/Func: snake_case).

### Testing
- **Factories:** `factories.py` is **MANDATORY**. Use `BaseModelTestMixin` to strictly verify logical deletion and `__str__` formats.
- **Coverage:** Include happy path, edge cases (max length, date chronology), and error handling.

### Templates
- Inherit from `common/base.html`. Modularize UI components into `common/includes/` to ensure DRY principles.

## 5. Operational Protocols
- **TODO Management:** Any technical debt or future enhancements identified during implementation **MUST** be recorded in `docs/TODO.md`.
- **Architectural Documentation:** Major design decisions, performance optimizations, and technical rationales (e.g., Mixin hierarchies, N+1 solutions) **MUST** be documented in `docs/ARCH_DESIGN.md` to ensure design transparency and knowledge transfer.
- **Architecture First:** Prioritize fixing structural or data model issues over local surgical fixes.

## 6. Primary Commands
- Test: `python library/manage.py test library`
- Quality: `ruff check .` / `mypy .`
- Database: `python library/manage.py makemigrations` / `migrate`

---

## 日本語訳・詳細解説 (Human-Readable Appendix)
<aside>
このセクションは開発者向けの参照用です。AIは上記の英語セクションを絶対的な指示として遵守してください。

### 1. プロジェクトの概要と目的
- **目標:** キャリアポートフォリオ。架空の会社のための分散型図書館アプリケーションのプロトタイプ。
- **課題:** 物理的な移動なしに、20フロアにわたる15,000冊を「仮想本棚」で管理すること。
- **UX制約:** 持ち出し防止とデータ整合性のため、場所の詳細は貸出または予約確定後にのみ表示されなければならない（MUST）。

### 2. ディレクトリ構成
- `library/`: プロジェクトルート。
  - `core/`: 抽象基盤。全アプリの共通規約。
  - `accounts/`: 認証、部署管理、権限。
  - `catalog/`: 静的データ（書誌、蔵書、場所、お気に入り）。
  - `transactions/`: 動的ライフサイクル（貸出・予約ロジック）。ミッションクリティカル。
  - `dashboard/`: 統合ポータルUI。アプリを跨いだデータの可視化。

### 3. 技術スタック
(Django 6.0.2, Python 3.14, Ruff, mypy 等を使用)

### 4. エンジニアリング基準
#### モデルとロジック
- **BaseModel継承:** 全モデルは `is_active` による論理削除を標準化するため `core.models.BaseModel` を継承しなければならない（MUST）。
- **ロジック配置:** 1.Model (Fat Model) > 2.Form > 3.Service の順に優先。Viewにビジネスロジックを実装してはならない（DO NOT / Thin View）。
- **命名:** PEP8に厳格に準拠（クラスは PascalCase、変数・関数は snake_case）。

#### テスト
- **Factory:** `factories.py` は必須（MANDATORY）。`BaseModelTestMixin` を使用して論理削除と `__str__` を厳密に検証すること。
- **網羅性:** 正常系、境界値、エラーハンドリングを含めること。

#### テンプレート
- `common/base.html` を継承。DRY原則のためUI部品は `common/includes/` でモジュール化すること。

### 5. 運用プロトコル
- **TODO管理:** 実装中に発見した技術的負債や将来の改善案は、必ず `docs/TODO.md` に記録しなければならない（MUST）。
- **設計の文書化:** 重要な設計判断、パフォーマンスの最適化、および技術的な根拠（Mixinの階層化、N+1の解決策など）は、設計の透明性と知識移転を確保するため、必ず `docs/ARCH_DESIGN.md` に文書化しなければならない（MUST）。
- **構造優先:** 局所的な修正よりも、構造的またはデータモデルの問題の解決を優先すること。
</aside>
