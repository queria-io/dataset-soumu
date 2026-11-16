{{ config(alias='source_file') }}

SELECT * FROM {{ ref('code_stg_source_file') }}
