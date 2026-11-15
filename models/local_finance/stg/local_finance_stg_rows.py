"""Excel の団体の行の都道府県名・団体名・団体コード。raw のセルから pipelines/settlement_layout.py で読む。"""

import csv
import tempfile

from pipelines.settlement_layout import COLUMNS, parse_cells


def model(dbt, session):
    dbt.config(alias="stg_rows")
    parsed = parse_cells(
        dbt.ref("local_finance_raw_cells").project("source_sha256, source_row, col_no, value").fetchall(),
        dbt.ref("local_finance_raw_merged_cells")
        .project("source_sha256, first_row, last_row, first_col, last_col")
        .fetchall(),
        dbt.ref("local_finance_raw_source_file").project("file_no, sha256, fiscal_year").fetchall(),
    )
    path = tempfile.NamedTemporaryFile(suffix=".csv", delete=False).name
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(parsed["rows"])
    return session.read_csv(path, header=False, columns=COLUMNS["rows"])
