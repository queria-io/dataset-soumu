{{ config(alias='source_file') }}

SELECT url, page_url, sha256, bytes, media_type, retrieved_at, etag, last_modified, fiscal_year, link_text
FROM {{ ref('local_finance_stg_source_file') }}
