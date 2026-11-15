"""Excel の団体の行の都道府県名・団体名・団体コード。raw のセルから pipelines/settlement_layout.py で読む。"""

import csv
import os
import sys
import tempfile

# dbt はリポジトリの直下で動くので、そこから pipelines を読めるようにする
sys.path.insert(0, os.getcwd())
from pipelines.settlement_layout import COLUMNS, parse_cells  # noqa: E402


def model(dbt, session):
    dbt.config(alias="stg_rows")
    parsed = parse_cells(
        dbt.ref("local_finance_raw_cells").fetchall(),
        dbt.ref("local_finance_raw_merged_cells").fetchall(),
        dbt.ref("local_finance_raw_files").fetchall(),
    )
    path = tempfile.NamedTemporaryFile(suffix=".csv", delete=False).name
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(parsed["rows"])
    return session.read_csv(path, header=False, columns=COLUMNS["rows"])
