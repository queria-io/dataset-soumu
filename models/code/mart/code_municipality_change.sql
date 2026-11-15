{{ config(alias='municipality_change') }}

-- 都道府県名を、コード一覧の都道府県の行で都道府県コードにし、3 桁のコードの前に付ける
SELECT
    c.effective_date,
    p.pref_code,
    c.pref_name,
    p.pref_code || c.old_local_code AS old_code,
    c.old_name,
    p.pref_code || c.new_local_code AS new_code,
    c.new_name,
    coalesce(starts_with(c.new_name, '削除'), false) AS is_code_deleted,
    c.reason,
    c.source_sha256
FROM {{ ref('code_stg_municipality_change') }} AS c
LEFT JOIN {{ ref('code_stg_municipality') }} AS p
    ON p.is_prefecture AND p.pref_name = c.pref_name
