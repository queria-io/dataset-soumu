{{ config(alias='stg_municipality_change') }}

SELECT
    CAST(effective_date AS DATE) AS effective_date,
    pref_code,
    pref_name,
    old_code,
    old_name,
    new_code,
    new_name,
    is_code_deleted,
    reason
FROM {{ ref('code_raw_municipality_change') }}
