{{ config(alias='stg_columns') }}

SELECT * FROM read_parquet('data/parquet/local_finance_stg_columns.parquet')
