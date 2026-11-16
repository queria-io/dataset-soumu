{{ config(alias='raw_source_file') }}

SELECT *
FROM read_json(
    'data/area_code/source_file.ndjson',
    columns = {
        url: 'VARCHAR',
        sha256: 'VARCHAR',
        bytes: 'BIGINT',
        media_type: 'VARCHAR',
        retrieved_at: 'VARCHAR',
        etag: 'VARCHAR',
        last_modified: 'VARCHAR',
        page_url: 'VARCHAR'
    },
    format = 'newline_delimited'
)
