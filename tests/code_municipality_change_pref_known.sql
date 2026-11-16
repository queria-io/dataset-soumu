-- 変更の履歴の都道府県名は、コード一覧の都道府県のどれかに当たる
SELECT pref_name
FROM {{ ref('code_municipality_change') }}
WHERE pref_code IS NULL
