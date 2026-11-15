{{ config(alias='stg_municipality') }}

-- district_name が NULL の行（郡に属さない市と特別区）は LIKE が NULL になり、
-- 階層区分の CASE では最後の municipality に入る。
SELECT
    area_code,
    pref_code,
    pref_name,
    district_name,
    municipality_name,
    yomigana,
    is_prefecture,
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
FROM {{ ref('code_raw_municipality') }}
