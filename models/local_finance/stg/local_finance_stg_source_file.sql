{{ config(alias='stg_source_file') }}

SELECT
    file_no,
    url,
    page_url,
    sha256,
    bytes,
    media_type,
    retrieved_at::TIMESTAMPTZ AS retrieved_at,
    etag,
    last_modified,
    fiscal_year,
    link_text
FROM {{ ref('local_finance_raw_source_file') }}
