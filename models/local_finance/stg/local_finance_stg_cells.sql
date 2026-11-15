{{ config(alias='stg_cells') }}

-- セルの値の前後の空白を除き、数値として読める値を数値にする。
-- 数値は全角の数字・符号と空白を正規化し、△・▲ を負の符号として読む。
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
