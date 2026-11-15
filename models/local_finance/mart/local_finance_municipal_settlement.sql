{{ config(alias='municipal_settlement') }}

-- raw_cells のうち、団体の行（stg_rows）と項目の列（stg_columns）が交わるセル。
-- 数値は全角の数字・符号と空白を正規化し、△・▲ を負の符号として読む。
-- 数値でない値の全角の「－」は「-」にする。
WITH cells AS (
    SELECT
        source_url,
        row_no,
        col_no,
        trim(value, ' 　') AS value,
        try_cast(
            translate(regexp_replace(value, '[\s　,，]', '', 'g'), '０１２３４５６７８９．－△▲', '0123456789.---')
            AS DOUBLE
        ) AS number
    FROM {{ ref('local_finance_raw_cells') }}
)

SELECT
    s.fiscal_year,
    s.entity_group,
    left(r.lg_code, 5) AS area_code,
    r.lg_code,
    r.pref_name,
    r.entity_name,
    s.section,
    c.item,
    c.unit,
    x.number AS value,
    CASE WHEN x.number IS NULL THEN translate(x.value, '－', '-') END AS value_text,
    s.source_url,
    s.page_url,
    x.row_no,
    x.col_no
FROM cells AS x
JOIN {{ ref('local_finance_stg_rows') }} AS r USING (source_url, row_no)
JOIN {{ ref('local_finance_stg_columns') }} AS c USING (source_url, col_no)
JOIN {{ ref('local_finance_stg_sheets') }} AS s USING (source_url)
WHERE x.value <> ''
