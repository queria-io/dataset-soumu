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

総務省の[市町村別決算状況調](https://www.soumu.go.jp/iken/kessan_jokyo_2.html)の Excel（2002 年度から最新の年度まで、都市別・町村別の概況・歳入内訳・目的別歳出内訳・性質別歳出内訳・地方債現在高等）を、1 行が 1 団体・1 年度・1 項目の縦持ちにしています。

| テーブル | 内容 |
| --- | --- |
| `local_finance.municipal_settlement` | 1 行が 1 団体・1 年度・1 項目。項目名・単位・値・出典の Excel の URL |

- 年度によって Excel の列の並びと見出しが違うので、見出しを親から順に「/」でつないだ項目名（`item`）にしています。見出しの番号（一・1・(1)・(ア)）と「内訳」は除いています
- 団体コード（`lg_code`）は Excel に団体コードがある 2011 年度から入っています。2010 年度までは都道府県名と団体名で団体を特定してください。その年度のコードが要るときは、下の例のように `codh.city.municipality`（歴史的行政区域）と有効期間で結合します
- 都道府県計・全国計などの合計の行は入っていません
- 取得は `pipelines/municipal_settlement.py` で行います。Excel は 1 秒に 1 回の頻度で取得します

```sql
-- 札幌市の歳入総額と地方税（千円）
SELECT fiscal_year, item, value
FROM soumu.local_finance.municipal_settlement
WHERE pref_name = '北海道' AND entity_name = '札幌市' AND item IN ('歳入総額', '地方税')
ORDER BY fiscal_year, item;
```

```sql
-- 2010 年度までの行に、その年度末（3 月 31 日）に有効だった団体コードを付ける
SELECT s.fiscal_year, s.pref_name, s.entity_name, coalesce(s.lg_code, m.lg_code) AS lg_code, s.item, s.value
FROM soumu.local_finance.municipal_settlement AS s
LEFT JOIN codh.city.municipality AS m
  ON s.lg_code IS NULL
 AND m.prefecture = s.pref_name
 AND m.full_name = s.entity_name
 AND NOT (m.suffix = '区' AND m.county_or_city IS NOT NULL)  -- 政令指定都市の区を除く
 AND m.valid_from <= make_date(s.fiscal_year + 1, 3, 31)
 AND coalesce(m.valid_to > make_date(s.fiscal_year + 1, 3, 31), true)
WHERE s.item = '歳入総額';
```

同じ都道府県に同じ名前の町村があった年度は、Excel の団体名に郡名が付いている（「一宮町・宍粟」）ので、この結合では当たりません。

## 出典と利用条件

- 行政事業レビュー見える化サイト（https://rssystem.go.jp）のレビューシートの URL を使っています
- 市町村別決算状況調は総務省「市町村別決算状況調」（https://www.soumu.go.jp/iken/kessan_jokyo_2.html）を加工して作成しています
- 各資料は総務省のウェブサイト（https://www.soumu.go.jp/）のコンテンツで、ウェブサイトの利用規約（政府標準利用規約）に従います。使うときは出典と加工したことを書いてください
- 図表には総務省以外の著作物が含まれることがあります。このデータセットは本文の文字だけを持ち、PDF の原本は保存していません

## ビルド

```bash
git submodule update --init
uv sync
bash scripts/build.sh
```
