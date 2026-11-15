{{ config(alias='raw_municipality_change') }}

-- 変更の履歴の Excel の行。A〜E 列の値を文字のまま読む
SELECT *
FROM read_json(
    'data/area_code/municipality_change.ndjson',
    columns = {
        source_sha256: 'VARCHAR',
        source_sheet: 'VARCHAR',
        source_row: 'INTEGER',
        col_1: 'VARCHAR',
        col_2: 'VARCHAR',
        col_3: 'VARCHAR',
        col_4: 'VARCHAR',
        col_5: 'VARCHAR'
    },
    format = 'newline_delimited'
)
