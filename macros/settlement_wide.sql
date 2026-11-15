{# 市町村別決算状況調の表 1 つ（section）を、1 行が 1 団体・1 年度、列が項目の横持ちにする。
   列は新しい年度の Excel の列の順に並べ、新しい年度に無い項目はその後ろに置く。
   国勢調査の値の項目（国勢調査人口・産業構造）は、先頭に「〈見出し〉/国勢調査の年」の列を置く。 #}
{% macro settlement_wide(section) %}
{% set items_sql %}
SELECT
    c.item,
    CASE WHEN bool_or(c.census_year IS NOT NULL) THEN split_part(c.item, '/', 1) END AS census_group
FROM {{ ref('local_finance_stg_columns') }} AS c
JOIN {{ ref('local_finance_stg_sheets') }} AS s USING (source_url)
WHERE s.section = '{{ section }}'
GROUP BY c.item
ORDER BY max(s.fiscal_year) DESC, arg_max(c.col_no, s.fiscal_year), c.item
{% endset %}
{% set rows = run_query(items_sql).rows if execute else [] %}
{% set seen = [] %}
SELECT
    fiscal_year,
    entity_group,
    area_code,
    lg_code,
    pref_name,
    entity_name,
    {%- for item, group in rows %}
    {%- if group and group not in seen %}
    {%- do seen.append(group) %}
    max(census_year) FILTER (WHERE split_part(item, '/', 1) = '{{ group | replace("'", "''") }}') AS "{{ group | replace('"', '""') }}/国勢調査の年",
    {%- endif %}
    max(value) FILTER (WHERE item = '{{ item | replace("'", "''") }}') AS "{{ item | replace('"', '""') }}",
    {%- endfor %}
    page_url
FROM {{ ref('local_finance_municipal_settlement') }}
WHERE section = '{{ section }}'
GROUP BY fiscal_year, entity_group, area_code, lg_code, pref_name, entity_name, page_url
{% endmacro %}
