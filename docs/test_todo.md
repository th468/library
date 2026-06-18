# Test Coverage Assessment & Action Items

本ドキュメントは、プロジェクト内の各アプリケーションにおけるテスト網羅性の精査結果と、今後の改善タスクをまとめたものです。全体としてテスト品質は高い水準にありますが、以下の改善項目を順次実装してください。

## 重要度ラベル
- **[高]**: 即時対応推奨（セキュリティ、データ整合性、ユーザー体験への直接的影響）
- **[中]**: 保守性向上（将来的なリスク低減）
- **[低]**: 設計・検討事項（データ量・ユーザー数増大時の対策）

---

## 1. core アプリケーション
- **`library/core/tests/test_tags.py`**
    - [ ] [中] テンプレートタグの内部ロジックだけでなく、`django.template.Template` を用いたテンプレートレンダリング結果（HTML出力）の検証を追加する。
- **`library/core/tests/test_mixins.py`**
    - [ ] [中] `RenameUniqueFieldsMixin` に対し、不正なフィールド指定（存在しないカラム等）に対する境界値テスト・エラーハンドリングの強化を行う。

## 2. catalog アプリケーション
- **`library/catalog/tests/test_views.py`**
    - [ ] **[高]** 論理削除されたデータが一覧画面等で誤って表示されないか、コンテキスト検証を強化する。
- **`library/catalog/tests/test_models.py`**
    - [ ] [低] `Book.save()` における `count` 採番時の競合リスクについて、`docs/TODO.md` に記録し、対策（トランザクション分離レベルの検討等）を策定する。

## 3. accounts アプリケーション
- **`library/accounts/tests/test_views.py`**
    - [ ] **[高]** パスワード変更画面における「古いパスワードの間違い」「脆弱な新パスワードのバリデーション」等の異常系テストを追加する。
- **`library/accounts/tests/test_models.py`**
    - [ ] **[高]** ユーザー権限（一般、スタッフ、スーパーユーザー）に基づく、モデルメソッド（`can_lend` 等）のアクセス制限テストを追加する。

## 4. transactions アプリケーション
- **`library/transactions/tests/test_views.py`**
    - [ ] **[高]** 他ユーザーの貸出・予約IDを指定した不正なPOSTリクエストに対し、403 Forbidden等の適切なエラーが返されるか権限チェックを追加する。
- **`library/transactions/tests/test_models.py`**
    - [ ] [低] `handle_expired_reservations` における大量データ処理時のパフォーマンスについて、`docs/ARCH_DESIGN.md` に懸念事項として記録し、バッチ処理化の検討を行う。

## 5. dashboard アプリケーション
- **`library/dashboard/tests.py`**
    - [ ] [中] ダッシュボードの各セクション（お気に入り、貸出中等）に正しいデータが反映されているか、コンテキストおよびHTML出力の検証を追加する。
- [ ] [低] リスト表示におけるページネーションの動作検証を追加する。
