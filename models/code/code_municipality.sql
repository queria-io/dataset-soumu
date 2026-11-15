{{ config(alias='municipality') }}

-- district_name が NULL の行（郡に属さない市と特別区）は LIKE が NULL になり、
-- 階層区分の CASE では最後の municipality に入る。
WITH src AS (
    SELECT *
    FROM read_json(
        'data/area_code/municipality.ndjson',
        columns = {
            area_code: 'VARCHAR',
            pref_code: 'VARCHAR',
            pref_name: 'VARCHAR',
            district_name: 'VARCHAR',
            municipality_name: 'VARCHAR',
            yomigana: 'VARCHAR',
            is_prefecture: 'BOOLEAN'
        },
        format = 'newline_delimited'
    )
),

classified AS (
    SELECT
        *,
        CASE
            WHEN is_prefecture THEN 'prefecture'
            WHEN municipality_name IS NULL AND district_name LIKE '%市' THEN 'designated_city'
            WHEN municipality_name IS NULL THEN 'district'
            WHEN district_name LIKE '%市' THEN 'ward'
            ELSE 'municipality'
        END AS area_kind,
        -- district_name には郡名・振興局名・支庁名・政令市名・「特別区部」が同居している
        CASE WHEN district_name LIKE '%郡' THEN district_name END AS county_name,
        CASE
            WHEN district_name LIKE '%振興局' OR district_name LIKE '%支庁'
                THEN district_name
        END AS subprefecture_name,
        CASE WHEN district_name LIKE '%市' THEN district_name END AS designated_city_name
    FROM src
)

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
FROM classified s
LEFT JOIN classified p
    ON s.area_kind = 'ward'
    AND p.area_kind = 'designated_city'
    AND p.pref_code = s.pref_code
    AND p.district_name = s.district_name
