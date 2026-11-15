{{ config(alias='stg_rows') }}

SELECT
    source_url,
    row_no,
    pref_name,
    entity_name,
    lg_code,
    left(lg_code, 5) AS area_code
FROM {{ ref('local_finance_raw_rows') }}
