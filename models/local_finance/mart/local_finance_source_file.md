---
$schema: https://queria.io/schemas/table/v1.json
table: local_finance.source_file
title: 市町村別決算状況調の取得したファイル
description: |-
  local_finance のテーブルの元にした総務省「市町村別決算状況調」の Excel の一覧です。1 行が 1 つのファイルで、同じ URL でも中身が変われば別の行になります。municipal_settlement の source_sha256 と sha256 で結合できます。
primary_key: [sha256]
sources:
  - path: https://www.soumu.go.jp/iken/kessan_jokyo_2.html
fields:
  - name: url
    title: 取得した URL
  - name: page_url
    title: 掲載されていた年度のページの URL
  - name: sha256
    title: ファイルの sha256
  - name: bytes
    title: バイト数
  - name: media_type
    title: メディアタイプ
  - name: retrieved_at
    title: 取得した日時（UTC）
  - name: etag
    title: 取得したときの ETag ヘッダー
  - name: last_modified
    title: 取得したときの Last-Modified ヘッダー
  - name: fiscal_year
    title: 決算年度（西暦）
  - name: link_text
    title: 年度のページのリンクの文字
---
