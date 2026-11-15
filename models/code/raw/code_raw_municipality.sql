{{ config(alias='raw_municipality') }}

-- コード一覧の CSV の行を、列名のまま読む
SELECT *
FROM read_json(
    'data/area_code/municipality.ndjson',
    columns = {
        source_sha256: 'VARCHAR',
        source_row: 'INTEGER',
        "ken-code": 'VARCHAR',
        "sityouson-code": 'VARCHAR',
        "tiiki-code": 'VARCHAR',
        "ken-name": 'VARCHAR',
        "sityouson-name1": 'VARCHAR',
        "sityouson-name2": 'VARCHAR',
        "sityouson-name3": 'VARCHAR',
        yomigana: 'VARCHAR'
    },
    format = 'newline_delimited'
)
