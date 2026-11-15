{{ config(alias='stg_sheets') }}

SELECT
    source_url,
    page_url,
    fiscal_year,
    entity_group,
    section,
    header_first_row,
    data_first_row,
    name_col,
    code_col
FROM {{ ref('local_finance_raw_sheets') }}
