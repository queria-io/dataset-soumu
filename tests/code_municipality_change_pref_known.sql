-- 変更の履歴の新コードの都道府県は、現行の一覧にある
SELECT c.new_code
FROM {{ ref('code_municipality_change') }} c
ANTI JOIN {{ ref('code_municipality') }} m
    ON m.area_code = c.pref_code || '000'
