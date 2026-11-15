{{ config(alias='municipal_settlement') }}

-- 団体の行（stg_rows）と項目の列（stg_columns）が交わるセル。
-- 数値でない値の全角の「－」は「-」にする。
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
    c.census_year,
    x.number AS value,
    CASE WHEN x.number IS NULL THEN translate(x.value, '－', '-') END AS value_text,
    s.source_url,
    s.page_url,
    x.row_no,
    x.col_no
FROM {{ ref('local_finance_stg_cells') }} AS x
JOIN {{ ref('local_finance_stg_rows') }} AS r USING (source_url, row_no)
JOIN {{ ref('local_finance_stg_columns') }} AS c USING (source_url, col_no)
JOIN {{ ref('local_finance_stg_sheets') }} AS s USING (source_url)
WHERE x.value <> ''
