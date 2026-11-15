{# 全角の空白を半角にして前後の空白を除く。空になれば NULL。 #}
{% macro clean_text(column) -%}
nullif(regexp_replace(replace({{ column }}, '　', ' '), '^\s+|\s+$', '', 'g'), '')
{%- endmacro %}
