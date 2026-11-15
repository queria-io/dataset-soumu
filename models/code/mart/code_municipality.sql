{{ config(alias='municipality') }}

SELECT
    s.area_code,
    s.pref_code,
    s.pref_name,
    s.district_name,
    s.municipality_name,
    s.yomigana,
    s.is_prefecture,
    s.area_kind,
    -- 市区町村として数えるのは市区町村と政令指定都市。行政区と集計行は数えない
    s.area_kind IN ('municipality', 'designated_city') AS is_municipality,
    s.county_name,
    s.subprefecture_name,
    s.designated_city_name,
    -- 行政区はその市のコード、市区町村と政令指定都市は自分自身（特別区も自分自身）
    CASE
        WHEN s.area_kind = 'ward' THEN p.area_code
        WHEN s.area_kind IN ('municipality', 'designated_city') THEN s.area_code
    END AS municipality_code
FROM {{ ref('code_stg_municipality') }} s
LEFT JOIN {{ ref('code_stg_municipality') }} p
    ON s.area_kind = 'ward'
    AND p.area_kind = 'designated_city'
    AND p.pref_code = s.pref_code
    AND p.district_name = s.district_name
