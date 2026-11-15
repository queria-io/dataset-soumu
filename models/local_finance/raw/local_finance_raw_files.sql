{{ config(alias='raw_files') }}

SELECT * FROM read_parquet('data/parquet/local_finance_raw_files.parquet')
