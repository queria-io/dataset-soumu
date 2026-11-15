{{ config(alias='stg_sheets') }}

SELECT * FROM read_parquet('data/parquet/local_finance_stg_sheets.parquet')
