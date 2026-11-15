{{ config(alias='municipal_settlement') }}

SELECT
    fiscal_year,
    entity_group,
    left(lg_code, 5) AS area_code,
    lg_code,
    pref_name,
    entity_name,
    section,
    item,
    unit,
    value,
    value_text,
    source_url,
    page_url
FROM read_parquet('data/parquet/local_finance_municipal_settlement.parquet')
