{{ config(alias='raw_sheets') }}

SELECT * FROM read_parquet('data/parquet/local_finance_raw_sheets.parquet')
