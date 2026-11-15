# 総務省

総務省のウェブサイト（www.soumu.go.jp）が公開する資料を収録した Queria のデータセット（`queria/soumu`）です。

## 計画・通知等（plans）


[行政事業レビュー見える化サイト](https://rssystem.go.jp)のレビューシート（政策・施策、法令等、2024 年度から）が「関係する計画・通知等」に挙げる URL のうち、総務省のサイト（www.soumu.go.jp）の PDF を取得し、ページごとの本文にしています。

| テーブル | 内容 |
| --- | --- |
| `plans.documents` | 1 行が 1 つの計画・通知等の PDF の URL。名前・sha256・ページ数・取得日時 |
| `plans.pages` | 1 行が 1 ページ。PDF から取り出して NFKC で正規化した本文 |

- 文字コードの対応表が無いフォントの文字は、Adobe-Japan1 の CID とみなして文字に戻しています（`cid_repaired_chars`）
- ほかのサイトの文書と HTML のページは入っていません。シートの URL のうち、取得できなかったもの（リンク切れなど）と開けない PDF も入っていません
- 全文検索の索引は持っていません。`plans.pages` の `text` を検索してください
- 取得と Parquet 化は dataset-shared の `review_plans.py` で行います。PDF は 1 秒に 1 回の頻度で取得します

## 地方財政（local_finance）

総務省の[市町村別決算状況調](https://www.soumu.go.jp/iken/kessan_jokyo_2.html)の Excel（2002 年度から最新の年度まで、都市別・町村別の概況・歳入内訳・目的別歳出内訳・性質別歳出内訳・地方債現在高等）を取り込んでいます。Excel のセルをそのまま持つテーブルから、見出しと団体の行を読み、縦持ちと表ごとの横持ちのテーブルを作ります。

| テーブル | 内容 |
| --- | --- |
| `local_finance.municipal_settlement` | 1 行が 1 団体・1 年度・1 項目の縦持ち。項目名・単位・値・出典の Excel の URL とセルの位置 |
| `local_finance.municipal_overview` | 概況の横持ち（人口・財政力指数・経常収支比率・実質収支など） |
| `local_finance.municipal_revenue` | 歳入内訳の横持ち |
| `local_finance.municipal_expenditure_by_purpose` | 目的別歳出内訳の横持ち |
| `local_finance.municipal_expenditure_by_nature` | 性質別歳出内訳の横持ち |
| `local_finance.municipal_debt` | 地方債現在高等の横持ち |
| `local_finance.municipal_town_expenditure` | 2006 年度までの町村の歳出内訳の横持ち |
| `local_finance.raw_cells` | Excel の空でないセルの値（文字のまま） |
| `local_finance.raw_merged_cells` | Excel の結合セルの範囲 |
| `local_finance.stg_sheets` | Excel ごとの年度・区分・表と、見出しと団体の行・列の位置 |
| `local_finance.stg_columns` | Excel の列ごとの項目名と単位 |
| `local_finance.stg_rows` | Excel の団体の行と、都道府県名・団体名・団体コード |

- 年度によって Excel の列の並びと見出しが違うので、見出しを親から順に「/」でつないだ項目名（`item`）にしています。見出しの番号（一・1・(1)・(ア)）と「内訳」は除いています。国勢調査人口と産業構造は見出しの国勢調査の年を外して `census_year` に置き（`国勢調査人口/令2.10.1` → `国勢調査人口`、2020）、「補てん」は「補塡」に統一しています。元の見出しは `stg_columns.heading` にあります。横持ちのテーブルでは、この項目名が列名です
- 項目は年度によって追加・廃止・改称されます。横持ちのテーブルでは、その年度の Excel に無い項目は NULL です
- `municipal_settlement` の `row_no`・`col_no` は元の Excel のセルの位置で、`raw_cells` と同じ番号です
- 団体コード（`lg_code`）は Excel に団体コードがある 2011 年度から入っています。2010 年度までは都道府県名と団体名で団体を特定してください。その年度のコードが要るときは、下の例のように `codh.city.municipality`（歴史的行政区域）と有効期間で結合します
- 都道府県計・全国計などの合計の行は、縦持ちと横持ちのテーブルには入っていません
- 取得は `pipelines/municipal_settlement.py` で行います。Excel は 1 秒に 1 回の頻度で取得します

```sql
-- 札幌市の地方税と地方債（千円）
SELECT fiscal_year, "地方税", "地方債"
FROM soumu.local_finance.municipal_revenue
WHERE pref_name = '北海道' AND entity_name = '札幌市'
ORDER BY fiscal_year;
```

```sql
-- 2010 年度までの行に、その年度末（3 月 31 日）に有効だった団体コードを付ける
SELECT s.fiscal_year, s.pref_name, s.entity_name, coalesce(s.lg_code, m.lg_code) AS lg_code, s."歳入総額"
FROM soumu.local_finance.municipal_overview AS s
LEFT JOIN codh.city.municipality AS m
  ON s.lg_code IS NULL
 AND m.prefecture = s.pref_name
 AND m.full_name = s.entity_name
 AND NOT (m.suffix = '区' AND m.county_or_city IS NOT NULL)  -- 政令指定都市の区を除く
 AND m.valid_from <= make_date(s.fiscal_year + 1, 3, 31)
 AND coalesce(m.valid_to > make_date(s.fiscal_year + 1, 3, 31), true);
```

同じ都道府県に同じ名前の町村があった年度は、Excel の団体名に郡名が付いている（「一宮町・宍粟」）ので、この結合では当たりません。

## 統計に用いる標準地域コード（code）

総務省の「[統計に用いる標準地域コード](https://www.soumu.go.jp/toukei_toukatsu/index/seido/9-5.htm)」のページに載る CSV と Excel を取得しています。

| テーブル | 内容 |
| --- | --- |
| `code.municipality` | 1 行が 1 つの標準地域コード（5 桁）。現行の都道府県・郡・政令指定都市・行政区・市区町村 |
| `code.municipality_change` | 1 行が 1 件のコードの変更（合併・編入・区の再編など）。2007 年 4 月 2 日以降 |

- 市区町村を数えるときは `is_municipality` で絞ります（政令指定都市は 1 団体、東京 23 区は 23 団体）
- 行政区の行の `municipality_code` は所属する政令指定都市のコードです。区ごとのデータを市にまとめるときに使います
- 全国地方公共団体コード（6 桁）の先頭 5 桁が標準地域コードです

```sql
SELECT area_code, pref_name, municipality_name
FROM soumu.code.municipality
WHERE is_municipality AND pref_name = '東京都'
```

## 出典と利用条件

- 行政事業レビュー見える化サイト（https://rssystem.go.jp）のレビューシートの URL を使っています
- 市町村別決算状況調は総務省「市町村別決算状況調」（https://www.soumu.go.jp/iken/kessan_jokyo_2.html）を加工して作成しています
- 標準地域コードは総務省「統計に用いる標準地域コード」（https://www.soumu.go.jp/toukei_toukatsu/index/seido/9-5.htm）を加工して作成しています
- 各資料は総務省のウェブサイト（https://www.soumu.go.jp/）のコンテンツで、ウェブサイトの利用規約（政府標準利用規約）に従います。使うときは出典と加工したことを書いてください
- 図表には総務省以外の著作物が含まれることがあります。このデータセットは本文の文字だけを持ち、PDF の原本は保存していません

## ビルド

```bash
git submodule update --init
uv sync
bash scripts/build.sh
```
