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
    f.url AS source_url,
    f.page_url,
    x.source_sha256,
    x.source_sheet,
    x.source_row AS row_no,
    x.col_no
FROM {{ ref('local_finance_stg_cells') }} AS x
JOIN {{ ref('local_finance_stg_rows') }} AS r USING (source_sha256, source_row)
JOIN {{ ref('local_finance_stg_columns') }} AS c USING (source_sha256, col_no)
JOIN {{ ref('local_finance_stg_sheets') }} AS s USING (source_sha256)
JOIN {{ ref('local_finance_stg_source_file') }} AS f ON f.sha256 = x.source_sha256
WHERE x.value <> ''
