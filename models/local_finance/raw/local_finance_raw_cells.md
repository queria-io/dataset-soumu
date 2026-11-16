---
$schema: https://queria.io/schemas/table/v1.json
table: local_finance.raw_cells
title: 市町村別決算状況調 Excel のセル
description: |-
  総務省「市町村別決算状況調」の Excel（1 ファイル 1 シート）の、空でないセルの値を文字のまま持つテーブルです。見出し・団体・合計・注記の行もすべて入っています。
primary_key: [source_sha256, source_row, col_no]
sources:
  - path: https://www.soumu.go.jp/iken/kessan_jokyo_2.html
fields:
  - name: source_sha256
    title: 元の Excel の sha256
    description: source_file の sha256
  - name: source_sheet
    title: 元の Excel のシート名
  - name: source_row
    title: 行番号
    description: 1 から数えた行番号
  - name: col_no
    title: 列番号
    description: 1 から数えた列番号（A 列が 1）
  - name: value
    title: セルの値
    description: Excel のセルの値の文字。数値は Excel が持つ値をそのまま文字にしています
published: false
---
