{{ config(alias='stg_municipality_change') }}

-- 変更の履歴の Excel を 1 件 1 行にする。
-- 見出し行（A 列が「都道府県」）より下に、影響を受ける市区町村が 1 行ずつ並び、各行の直後によみがなの行が続く。
-- 都道府県・改正事由・施行年月日は 1 つの改正の先頭行にだけあるので、下の行へ送る。
-- 旧コードの欄にある見出し（「参考：支庁から…」など、コードでもよみがなでもない文字）は、その下の変更の改正事由にする。
WITH cells AS (
    SELECT
        source_sha256,
        source_sheet,
        source_row,
        {{ clean_text('col_1') }} AS pref_cell,
        {{ clean_text('col_2') }} AS old_cell,
        {{ clean_text('col_3') }} AS new_cell,
        {{ clean_text('col_4') }} AS reason_cell,
        left({{ clean_text('col_5') }}, 10) AS date_cell
    FROM {{ ref('code_raw_municipality_change') }}
),

body AS (
    SELECT c.*
    FROM cells AS c
    WHERE c.source_row > (
        SELECT min(h.source_row) FROM cells AS h
        WHERE h.source_sha256 = c.source_sha256 AND h.pref_cell = '都道府県'
    )
),

filled AS (
    SELECT
        *,
        last_value(pref_cell IGNORE NULLS) OVER w AS pref_name,
        last_value(
            coalesce(reason_cell, CASE WHEN NOT regexp_matches(old_cell, '^[0-9０-９（(]') THEN old_cell END)
            IGNORE NULLS
        ) OVER w AS reason,
        last_value(date_cell IGNORE NULLS) OVER w AS effective_date
    FROM body
    WINDOW w AS (PARTITION BY source_sha256 ORDER BY source_row ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
)

-- 「309 飯野町」をコード（都道府県の中の 3 桁）と名前に分ける。新コードの欄に数字がある行だけを取り出す
SELECT
    CAST(effective_date AS DATE) AS effective_date,
    pref_name,
    nullif(regexp_extract(old_cell, '^([0-9]+)', 1), '') AS old_local_code,
    CASE
        WHEN regexp_matches(old_cell, '^[0-9]+') THEN nullif(regexp_extract(old_cell, '^[0-9]+\s*(.*)$', 1), '')
        ELSE old_cell
    END AS old_name,
    nullif(regexp_extract(new_cell, '^([0-9]+)', 1), '') AS new_local_code,
    CASE
        WHEN regexp_matches(new_cell, '^[0-9]+') THEN nullif(regexp_extract(new_cell, '^[0-9]+\s*(.*)$', 1), '')
        ELSE new_cell
    END AS new_name,
    reason,
    source_sha256,
    source_sheet,
    source_row
FROM filled
WHERE regexp_matches(new_cell, '[0-9０-９]')
