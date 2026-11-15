{# 市町村別決算状況調の表 1 つ（section）を、1 行が 1 団体・1 年度、列が項目の横持ちにする。
   列は新しい年度の Excel の列の順に並べ、新しい年度に無い項目はその後ろに置く。 #}
{% macro settlement_wide(section) %}
{% set items_sql %}
SELECT c.item
FROM {{ ref('local_finance_stg_columns') }} AS c
JOIN {{ ref('local_finance_stg_sheets') }} AS s USING (source_url)
WHERE s.section = '{{ section }}'
GROUP BY c.item
ORDER BY max(s.fiscal_year) DESC, arg_max(c.col_no, s.fiscal_year), c.item
{% endset %}
{% set items = run_query(items_sql).columns[0].values() if execute else [] %}
SELECT
    fiscal_year,
    entity_group,
    area_code,
    lg_code,
    pref_name,
    entity_name,
    {%- for item in items %}
    max(value) FILTER (WHERE item = '{{ item }}') AS "{{ item }}",
    {%- endfor %}
    page_url
FROM {{ ref('local_finance_municipal_settlement') }}
WHERE section = '{{ section }}'
GROUP BY fiscal_year, entity_group, area_code, lg_code, pref_name, entity_name, page_url
{% endmacro %}
