{{ config(alias='stg_columns') }}

SELECT
    source_sha256,
    col_no,
    heading,
    item,
    census_year,
    unit
FROM {{ ref('local_finance_raw_columns') }}
