{{ config(alias='raw_columns') }}

SELECT * FROM read_parquet('data/parquet/local_finance_raw_columns.parquet')
