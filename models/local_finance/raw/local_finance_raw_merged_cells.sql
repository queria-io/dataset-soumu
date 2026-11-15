{{ config(alias='raw_merged_cells') }}

SELECT * FROM read_parquet('data/parquet/local_finance_raw_merged_cells.parquet')
