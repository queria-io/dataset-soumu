{{ config(alias='municipality_change') }}

SELECT * FROM {{ ref('code_stg_municipality_change') }}
