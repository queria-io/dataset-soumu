-- 横持ちのテーブルで 1 団体・1 年度・1 表が 1 行になる（区分・団体コード・年度のページが 1 つ）
SELECT section, fiscal_year, pref_name, entity_name
FROM {{ ref('local_finance_municipal_settlement') }}
GROUP BY ALL
HAVING count(DISTINCT (entity_group, lg_code, page_url)) > 1
