---
$schema: https://queria.io/schemas/table/v1.json
table: code.municipality_change
title: 標準地域コードの変更（廃置分合）履歴
description: |-
  標準地域コードの変更（合併・編入・区の再編など）を、旧コードから新コードへの対応として1件1行で持つテーブルです。

  - 収録は2007年4月2日以降だけで、平成の大合併のピーク（1999〜2006年）は含みません
keywords:
  - 総務省
  - 標準地域コード
  - 廃置分合
  - 市町村合併
sources:
  - path: https://www.soumu.go.jp/toukei_toukatsu/index/seido/9-5.htm
fields:
  - name: effective_date
    title: 施行年月日
    description: 変更の施行年月日。収録は2007年4月2日以降のみで、平成の大合併のピーク（1999〜2006年）は含まない
  - name: pref_code
    title: 都道府県コード（2桁）
    description: 都道府県コード（2桁）
    semantic: {role: entity, name: prefecture}
  - name: pref_name
    title: 都道府県名
    description: 都道府県名
  - name: old_code
    title: 旧標準地域コード（5桁。新設の場合は空）
    description: 変更前の標準地域コード（5桁）。新設の場合は空。編入・合併で消滅したコードの行では new_code も同じコードで、編入先・合併後のコードはこの表に無く reason の文面にだけ書かれる
  - name: old_name
    title: 旧市区町村名（新設の場合は空）
    description: 変更前の市区町村名。新設の場合は空
  - name: new_code
    title: 新標準地域コード（5桁）
    description: 変更後の標準地域コード（5桁）。code.municipality の area_code と同体系。is_code_deleted が真の行では消滅した old_code と同じ値で、現行の一覧には無い
  - name: new_name
    title: 新市区町村名。編入・合併で消滅した場合は「削除」表記
    description: 変更後の市区町村名。編入・合併でコードが消滅した場合は「削除」と入る
  - name: is_code_deleted
    title: 当該コードが削除（編入・合併で消滅）されたか
    description: 当該コードが編入・合併で消滅したかどうか。真なら old_code は現行コード一覧に存在しない
  - name: reason
    title: 改正事由（合併・編入等の内容）
    description: 改正事由の原文（「熊毛郡上屋久町、屋久町を合併し、屋久島町を新設」など）。北海道の支庁から振興局への名称変更（2010年4月1日）の行は、元の表の見出し「参考：支庁から総合振興局又は振興局への変更」が入る。合併・編入・名称変更のどれかは、この文面から読み取る
  - name: source_sha256
    title: 元のファイルの sha256
    description: source_file の sha256
themes: [land_climate]
---
