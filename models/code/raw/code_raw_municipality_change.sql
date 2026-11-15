{{ config(alias='raw_municipality_change') }}

SELECT *
FROM read_json(
    'data/area_code/municipality_change.ndjson',
    columns = {
        effective_date: 'VARCHAR',
        pref_code: 'VARCHAR',
        pref_name: 'VARCHAR',
        old_code: 'VARCHAR',
        old_name: 'VARCHAR',
        new_code: 'VARCHAR',
        new_name: 'VARCHAR',
        is_code_deleted: 'BOOLEAN',
        reason: 'VARCHAR'
    },
    format = 'newline_delimited'
)
