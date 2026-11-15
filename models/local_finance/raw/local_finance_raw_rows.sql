{{ config(alias='raw_rows') }}

SELECT * FROM read_parquet('data/parquet/local_finance_raw_rows.parquet')
