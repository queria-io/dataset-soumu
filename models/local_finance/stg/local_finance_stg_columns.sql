{{ config(alias='stg_columns') }}

SELECT
    source_url,
    col_no,
    heading,
    item,
    census_year,
    unit
FROM {{ ref('local_finance_raw_columns') }}
