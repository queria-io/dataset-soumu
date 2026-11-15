{{ config(alias='stg_rows') }}

SELECT * FROM read_parquet('data/parquet/local_finance_stg_rows.parquet')
