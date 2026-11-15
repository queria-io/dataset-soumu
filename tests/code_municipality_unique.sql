-- 標準地域コード 1 つに 1 行
SELECT area_code
FROM {{ ref('code_municipality') }}
GROUP BY ALL
HAVING count(*) > 1
