{{ config(alias='raw_municipality') }}

SELECT *
FROM read_json(
    'data/area_code/municipality.ndjson',
    columns = {
        area_code: 'VARCHAR',
        pref_code: 'VARCHAR',
        pref_name: 'VARCHAR',
        district_name: 'VARCHAR',
        municipality_name: 'VARCHAR',
        yomigana: 'VARCHAR',
        is_prefecture: 'BOOLEAN'
    },
    format = 'newline_delimited'
)
