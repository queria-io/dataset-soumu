{{ config(alias='raw_source_file') }}

SELECT * FROM read_parquet('data/parquet/local_finance_raw_source_file.parquet')
