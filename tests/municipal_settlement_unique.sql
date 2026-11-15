-- 1 団体・1 年度・1 項目に 1 行
SELECT fiscal_year, pref_name, entity_name, section, item
FROM {{ ref('local_finance_municipal_settlement') }}
GROUP BY ALL
HAVING count(*) > 1
