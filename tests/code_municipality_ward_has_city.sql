-- 行政区はすべて所属する政令指定都市のコードを持つ
SELECT area_code
FROM {{ ref('code_municipality') }}
WHERE area_kind = 'ward' AND municipality_code IS NULL
