
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0.2-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Code_Style](https://img.shields.io/badge/Code__Style-Ruff-black?style=flat-square)](https://github.com/astral-sh/ruff)
[![Database](https://img.shields.io/badge/Database-SQLite3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org/)

# DecenLib - 分散型図書管理システム

## 概要
オフィス内などで分散する書籍をローコストで有効活用する、分散型図書館Webアプリケーション

<img width="2400" height="1350" alt="ダッシュボード" src="https://github.com/user-attachments/assets/8f59ed48-6290-4d47-841d-bda34f6a7e97" />


## URL

(URL)

テスト用ログインユーザー情報：（）

---

## プロジェクトの背景と課題

このプロジェクトは、アプリケーション開発の一連の流れを学習することを目的として、架空の企業からの依頼を想定し、作成したものです。

*   **課題**:多数のフロアや棚に分散した蔵書を活用したいが、専用のスペースや人員を用意する余裕がない。

*   **解決策**: ウェブアプリケーション上で書籍の表示、検索機能を実装することで、物理的には分散させたまま、必要な書籍へのアクセスを可能にする。  
また、アプリケーション内で貸出、返却機能を実装することで、利用者の端末のみで貸し借りのサイクルを完結させ、司書の常駐を不要とした。


---

## アプリケーションのイメージ

| トップ画面 |　ログイン画面 |
| ---- | ---- |
| <img width="2400" height="1350" alt="イントロダクション" src="https://github.com/user-attachments/assets/5d3e9786-3bc3-4921-ad70-bcebe25c4838" /> | <img width="2400" height="1350" alt="ログイン" src="https://github.com/user-attachments/assets/4e1f49cf-5804-48de-b794-a2a4c97a403b" />|
|  |  |

| ダッシュボード |　書籍詳細 |
| ---- | ---- |
|<img width="2400" height="1350" alt="ダッシュボード" src="https://github.com/user-attachments/assets/8f59ed48-6290-4d47-841d-bda34f6a7e97" /> |<img width="2400" height="1350" alt="書籍詳細" src="https://github.com/user-attachments/assets/c98dbc2d-c58e-4263-a4fd-2d6a2e9e454c" />|
|  |  |

| 書籍一覧 |　ユーザーページ |
| ---- | ---- |
| <img width="2400" height="1350" alt="書籍一覧" src="https://github.com/user-attachments/assets/3332454d-9da6-4cfe-8a60-92144f9bcdc2" /> | <img width="2400" height="1350" alt="書籍詳細" src="https://github.com/user-attachments/assets/c98dbc2d-c58e-4263-a4fd-2d6a2e9e454c" />|
|  |  |

---

##  技術的ハイライト & アーキテクチャ設計



### 1. Basemodelクラスの継承によって、論理削除等の基本機能を全モデル共通実装

django標準のmodels.modelを継承したBasemodelクラス及び

### 2. データーの取得を、ビューが継承したmixinによって行うことでN＋１問題を解決


### 3. 実在の書籍と書誌情報の分離

### 4.書誌情報に対して予約を作成し、その後実在書籍に引き当てるロジック構築

##  将来の拡張ロードマップ (TODO)

本プロジェクトは以下の機能拡張を将来の課題として想定しています。

1.  **通知システム**: 予約書籍の準備完了通知や返却期限警告の自動通知機能。
2.  **外部API連携**: Google Books API等と連携し、ISBN入力による書籍情報の自動取得。
3.  **非同期UXの向上**: `htmx` を用いた「お気に入り登録」や「貸出申請」の非同期 (Ajax) 通信化。
4.  **E2Eテスト作成**: praywright等を用いたE2Eテストの作成。




##  技術スタック

*   **言語/フレームワーク**: Python 3.14 / Django 6.0.2
*   **フロントエンド**: HTML5 / Vanilla CSS / Bootstrap 5 / django-widget-tweaks
*   **静的解析・品質保証**: Ruff (Linter & Formatter) 
*   **データベース**: SQLite3
*   **テスト・シードデータ**: factory_boy / Faker

---





##  データモデル設計

### 2.1. ER図

全 10 モデルのリレーションを示します。

```mermaid
erDiagram
    %% --- accounts アプリ ---
    User {
        int     id              PK
        string  em_num          UK "社員番号"
        string  email           UK "メールアドレス"
        bool    is_active           "有効フラグ"
        bool    is_staff            "管理者フラグ"
        int     lending_limit       "貸出上限冊数"
        int     lending_period_days "貸出可能日数"
        string  name                "氏名"
        int     department_id   FK
        datetime created_at
        datetime updated_at
    }
    Department {
        int     id   PK
        string  name "部署名"
        bool    is_active
        datetime created_at
        datetime updated_at
    }

    %% --- catalog アプリ ---
    Biblio {
        int     id            PK
        string  isbn          UK
        string  title
        string  author
        string  publisher
        string  published_date
        text    description
        image   cover
        bool    is_active
        datetime created_at
        datetime updated_at
    }
    Category {
        int    id   PK
        string name UK
        bool   is_active
    }
    Book {
        int id          PK
        int biblio_id   FK
        int shelf_id    FK
        int count           "管理番号（同一書誌内通し番号）"
        int status          "1:在庫あり 2:貸出中 3:予約中 4:ﾒﾝﾃﾅﾝｽ 5:紛失"
        bool is_active
        datetime created_at
        datetime updated_at
    }
    Shelf {
        int   id       PK
        int   floor_id FK
        string name
        text  description
        image location_photo
        bool  is_active
    }
    Floor {
        int   id  PK
        string name
        image map
        bool  is_active
    }
    Favorite {
        int id       PK
        int user_id  FK
        int biblio_id FK
        bool is_active
        datetime created_at
    }

    %% --- transactions アプリ ---
    Lending {
        int  id          PK
        int  user_id     FK
        int  book_id     FK
        date due_date       "返却期限"
        date return_date    "返却日（null=貸出中）"
        int  status         "1:貸出中 2:返却済み 3:その他"
        bool is_active
        datetime created_at
        datetime updated_at
    }
    Reservation {
        int  id             PK
        int  user_id        FK
        int  biblio_id      FK
        int  book_id        FK "null許容: 準備完了後に引き当て"
        int  status             "1:入荷待ち 2:準備完了 3:貸出済み 4:ｷｬﾝｾﾙ 5:期限切れ"
        date reserved_until     "取置期限（READY 後にセット）"
        bool is_active
        datetime created_at
        datetime updated_at
    }

    %% --- リレーション定義 ---
    User        }o--o|  Department  : "所属"
    User        ||--o{  Lending     : "借りる"
    User        ||--o{  Reservation : "予約する"
    User        ||--o{  Favorite    : "お気に入り登録"

    Biblio      }o--o{  Category    : "分類される（M2M）"
    Biblio      ||--o{  Book        : "実体を持つ"
    Biblio      ||--o{  Reservation : "予約される"
    Biblio      ||--o{  Favorite    : "お気に入りされる"

    Book        }o--||  Shelf       : "配架される"
    Book        ||--o{  Lending     : "貸し出される"
    Book        ||--o{  Reservation : "取置される（null許容）"

    Shelf       }o--||  Floor       : "属するフロア"
```


---



## 5. クイックスタート (セットアップ・起動手順)



ローカル環境で本システムを起動するための手順です。

### 5.1. 依存パッケージのインストール
仮想環境を作成・アクティベートした状態で、以下のコマンドを実行します。
```bash
pip install -r requirements.txt
```

### 5.2. データベースマイグレーション
データベースの初期化とテーブル作成を行います。
```bash
python library/manage.py migrate
```

### 5.3. デモデータの自動生成（シードデータの挿入）
FakerとFactory Boyを利用し、テスト用のダミーデータ（部署、ユーザー、本棚、蔵書、貸出履歴など）を一括生成します。
```bash
python library/seed_data.py
```
> [!WARNING]
> このスクリプトを実行すると、既存のデータベースレコード（管理者以外の全データ）が一掃（`hard_delete`）され、新しく再生成されます。

**自動生成されるデフォルトアカウント**:
*   管理者アカウント: `admin@example.com` / パスワード: `password123`

### 5.4. ローカルサーバーの起動
```bash
python library/manage.py runserver
```
起動後、ブラウザで `http://127.0.0.1:8000/` にアクセスして動作を確認します。

---

###  品質保証 & テスト実行


コード品質を担保するため、静的解析ツールと単体テストを導入しています。

*   **単体テストの実行**:
    ```bash
    python library/manage.py test library
    ```
*   **コードの整形・静的解析 (Linter / Formatter)**:
    ```bash
    ruff check .
    ```

---
