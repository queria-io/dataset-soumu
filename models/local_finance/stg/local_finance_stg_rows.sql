{{ config(alias='stg_rows') }}

SELECT
    source_sha256,
    source_row,
    pref_name,
    entity_name,
    lg_code
FROM {{ ref('local_finance_raw_rows') }}
