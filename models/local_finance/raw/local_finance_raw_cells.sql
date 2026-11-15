{{ config(alias='raw_cells') }}

SELECT * FROM read_parquet('data/parquet/local_finance_raw_cells.parquet')
