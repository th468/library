### 📝 テーブル定義一覧

| テーブル名 (物理) | テーブル名 (論理) | 説明 |
| :--- | :--- | :--- |
| なし | 基底モデル | 論理削除やstrメソッドなど基本的な振る舞いを定義した抽象モデル。見やすさのため省略しているが、`User` 以外の全てのテーブルはこのテーブルと同様のフィールドを持っている。
| `User` | ユーザー | システムを利用する社員情報。貸出上限などの制御も含む。 |
| `Department` | 部署 | 社員の所属する部署マスター。 |
| `Biblio` | 書誌 | 本のタイトル、ISBN、著者など、作品としての基本情報。 |
| `Category` | カテゴリ | 本のジャンル・分類マスター。 |
| `Book` | 蔵書 | 図書館が実際に所有している「本」そのものの情報（個体管理）。 |
| `Shelf` | 本棚 | 本が置かれている棚の情報。 |
| `Floor` | フロア | 本棚が設置されている階の情報。 |
| `Favorite` | お気に入り | ユーザーが気になる書誌を登録する中間テーブル。 |
| `Lending` | 貸出履歴 | 本の貸出状況、返却期限、返却日などを管理。 |
| `Reservation` | 予約 | 本の予約状況、取置期限などを管理。 |


### 📝 ER図
```mermaid
erDiagram
		BaseModel {
				bool    is_active           "有効フラグ"
				datetime created_at
        datetime updated_at
        }

    %% --- accounts アプリ ---
    User {
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
        string  name "部署名"
    }

    %% --- catalog アプリ ---
    Biblio {
        string  isbn          UK
        string  title
        string  author
        string  publisher
        string  published_date
        text    description
        image   cover
    }
    Category {
        string name UK
    }
    Book {
        int biblio_id   FK
        int shelf_id    FK
        int count           "管理番号（同一書誌内通し番号）"
        int status          "1:在庫あり 2:貸出中 3:予約中 4:ﾒﾝﾃﾅﾝｽ 5:紛失"
    }
    Shelf {
        int   floor_id FK
        string name
        text  description
        image location_photo
    }
    Floor {
        string name
        image map
    }
    Favorite {
        int user_id  FK
        int biblio_id FK
    }

    %% --- transactions アプリ ---
    Lending {
        int  user_id     FK
        int  book_id     FK
        date due_date       "返却期限"
        date return_date    "返却日（null=貸出中）"
        int  status         "1:貸出中 2:返却済み 3:その他"
    }
    Reservation {
        int  user_id        FK
        int  biblio_id      FK
        int  book_id        FK "null許容: 準備完了後に引き当て"
        int  status             "1:入荷待ち 2:準備完了 3:貸出済み 4:ｷｬﾝｾﾙ 5:期限切れ"
        date reserved_until     "取置期限（READY 後にセット）"
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