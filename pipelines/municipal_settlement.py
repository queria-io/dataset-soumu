"""総務省の市町村別決算状況調（平成14年度から）の Excel を取得し、セルの Parquet にする。

年度ごとのページ（https://www.soumu.go.jp/iken/kessan_jokyo_2.html から辿る）に、
都市別・町村別の (1) 概況 (2) 歳入内訳 (3) 目的別歳出内訳 (4) 性質別歳出内訳 (5) 地方債現在高等 の
Excel がある。取得したファイルの一覧（source_file）と、Excel の空でないセルと結合セルの範囲を
そのまま表にし、あわせて見出しから列ごとの項目名を作り、団体の行を見つける（pipelines/settlement_layout.py）。

出典: 総務省「市町村別決算状況調」 https://www.soumu.go.jp/iken/kessan_jokyo_2.html
"""

import contextlib
import csv
import io
import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import duckdb
import openpyxl
import xlrd

from pipelines.settlement_layout import COLUMNS as LAYOUT_COLUMNS
from pipelines.settlement_layout import parse
from shared.fetch import fetch, fetch_file, write_atomic

logger = logging.getLogger("pipelines")

USER_AGENT = "queria-dataset-soumu (+https://queria.io/)"
INDEX_URL = "https://www.soumu.go.jp/iken/kessan_jokyo_2.html"
RAW_DIR = Path("data/municipal_settlement")
PARQUET_DIR = Path("data/parquet")
# 総務省のサイトへは 1 秒に 1 回まで
INTERVAL = 1.0

def get(url: str) -> bytes:
    time.sleep(INTERVAL)
    return fetch(url, user_agent=USER_AGENT)


def fiscal_year(title: str) -> int:
    """「令和6年度」「令和元年度」「平成30年度」を西暦の年度にする。"""
    era, year = re.search(r"(令和|平成)(元|\d+)年度", title).groups()
    return (2018 if era == "令和" else 1988) + (1 if year == "元" else int(year))


def links(html: str, pattern: str) -> list[tuple[str, str]]:
    return [
        (href, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).strip())
        for href, text in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S)
        if re.search(pattern, href)
    ]


def list_files() -> list[dict]:
    """年度ごとのページから Excel の URL を集める。参考資料は除く。"""
    index = get(INDEX_URL).decode("cp932")
    pages = [
        (urljoin(INDEX_URL, href), title)
        for href, title in links(index, r"/zaisei/[^/]+\.html$")
        if title.endswith("市町村別決算状況調")
    ]
    files = {}
    for page_url, title in pages:
        html = get(page_url).decode("cp932")
        # 同じ Excel への 2 つ目のリンクは読まない（1 つのファイルを 2 回取り込むと行が重複する）
        for href, text in links(html, r"(?i)\.xlsx?$"):
            url = urljoin(page_url, href)
            if "参考" not in text and url not in files:
                files[url] = {
                    "fiscal_year": fiscal_year(title),
                    "page_url": page_url,
                    "url": url,
                    "link_text": text,
                }
    return list(files.values())


def local_path(url: str) -> Path:
    return RAW_DIR / re.sub(r"[^\w.]", "_", url.split("soumu.go.jp/", 1)[1])


def download() -> None:
    """Excel を取得し、取得したファイルの一覧を source_file.json に書く。

    前回の一覧の行があり手元にファイルがあれば条件付き GET を送り、変わっていなければ取得しない。
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    record = RAW_DIR / "source_file.json"
    previous = (
        {row["url"]: row for row in json.loads(record.read_text(encoding="utf-8"))}
        if record.exists()
        else {}
    )
    rows = []
    for file_no, file in enumerate(list_files(), 1):
        time.sleep(INTERVAL)
        fetched = fetch_file(
            file["url"], local_path(file["url"]), previous=previous.get(file["url"]), user_agent=USER_AGENT
        )
        # 一覧の並び（file_no）は、区分の書かれていないシートが前のファイルの区分を引き継ぐのに使う
        rows.append({**fetched, **file, "file_no": file_no})
    write_atomic(record, json.dumps(rows, ensure_ascii=False, indent=1))
    logger.info("municipal_settlement: %d ファイル", len(rows))


# ---- Excel を読む ----


def read_grid(
    content: bytes, url: str
) -> tuple[str, list[list], list[tuple[int, int, int, int]]]:
    """最初のシートの名前とセルの値と、結合セルの範囲（行の始まり・終わりの次・列の始まり・
    終わりの次、0 始まり）を返す。"""
    if url.lower().endswith(".xlsx"):
        sheet = openpyxl.load_workbook(io.BytesIO(content), data_only=True).worksheets[0]
        grid = [list(row) for row in sheet.iter_rows(values_only=True)]
        ranges = [
            (r.min_row - 1, r.max_row, r.min_col - 1, r.max_col) for r in sheet.merged_cells.ranges
        ]
        name = sheet.title
    else:
        sheet = xlrd.open_workbook(file_contents=content, formatting_info=True).sheet_by_index(0)
        grid = [sheet.row_values(i) for i in range(sheet.nrows)]
        ranges = sheet.merged_cells
        name = sheet.name
    return name, grid, sorted(ranges)


def raw_text(value) -> str | None:
    """セルの値をそのまま文字にする。整数の浮動小数点数は小数点を付けない。空のセルは None。"""
    if value is None or value == "":
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


# 取得したファイルの一覧（source_file.json）の列
SOURCE_FILE = {
    "file_no": "INTEGER",
    "url": "VARCHAR",
    "page_url": "VARCHAR",
    "sha256": "VARCHAR",
    "bytes": "BIGINT",
    "media_type": "VARCHAR",
    "retrieved_at": "VARCHAR",
    "etag": "VARCHAR",
    "last_modified": "VARCHAR",
    "fiscal_year": "INTEGER",
    "link_text": "VARCHAR",
}

# Parquet にするテーブルと列。行番号・列番号は Excel と同じ 1 始まり
TABLES_OUT = {
    "raw_cells": {
        "source_sha256": "VARCHAR",
        "source_sheet": "VARCHAR",
        "source_row": "INTEGER",
        "col_no": "INTEGER",
        "value": "VARCHAR",
    },
    "raw_merged_cells": {
        "source_sha256": "VARCHAR",
        "source_sheet": "VARCHAR",
        "first_row": "INTEGER",
        "last_row": "INTEGER",
        "first_col": "INTEGER",
        "last_col": "INTEGER",
    },
    # 見出しと団体の行の読み取り（settlement_layout.parse）
    **{f"raw_{name}": columns for name, columns in LAYOUT_COLUMNS.items()},
}


def build_parquet() -> None:
    record = RAW_DIR / "source_file.json"
    files = json.loads(record.read_text(encoding="utf-8"))
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    spec = ", ".join(f"'{column}': '{type_}'" for column, type_ in SOURCE_FILE.items())
    duckdb.execute(
        f"COPY (SELECT * FROM read_json('{record}', format = 'array', columns = {{{spec}}}))"
        f" TO '{PARQUET_DIR / 'local_finance_raw_source_file.parquet'}' (FORMAT parquet)"
    )
    # セルの数が 1 千万を超えるので、CSV に書いてから DuckDB で Parquet にする
    paths = {name: RAW_DIR / f"{name}.csv" for name in TABLES_OUT}
    with contextlib.ExitStack() as stack:
        writers = {
            name: csv.writer(stack.enter_context(path.open("w", newline="", encoding="utf-8")))
            for name, path in paths.items()
        }
        category = None
        for file in sorted(files, key=lambda file: file["file_no"]):
            sha256 = file["sha256"]
            sheet, grid, ranges = read_grid(local_path(file["url"]).read_bytes(), file["url"])
            writers["raw_cells"].writerows(
                (sha256, sheet, r + 1, c + 1, text)
                for r, row in enumerate(grid)
                for c, value in enumerate(row)
                if (text := raw_text(value)) is not None
            )
            writers["raw_merged_cells"].writerows(
                (sha256, sheet, r0 + 1, r1, c0 + 1, c1) for r0, r1, c0, c1 in ranges
            )
            # 結合セルの各セルから左上のセルへの対応
            merged = {
                (r, c): (r0, c0) for r0, r1, c0, c1 in ranges for r in range(r0, r1) for c in range(c0, c1)
            }
            # 区分の書かれていないシートは、一覧で前のファイルの区分を引き継ぐ
            layout = parse(grid, merged, file, category)
            category = layout["category"]
            writers["raw_sheets"].writerow(layout["sheet"])
            writers["raw_columns"].writerows(layout["columns"])
            writers["raw_rows"].writerows(layout["rows"])
    for name, columns in TABLES_OUT.items():
        spec = ", ".join(f"'{column}': '{type_}'" for column, type_ in columns.items())
        duckdb.execute(
            f"COPY (SELECT * FROM read_csv('{paths[name]}', header = false, quote = '\"',"
            f" escape = '\"', columns = {{{spec}}}))"
            f" TO '{PARQUET_DIR / f'local_finance_{name}.parquet'}' (FORMAT parquet, COMPRESSION zstd)"
        )
        paths[name].unlink()
    logger.info("municipal_settlement: %d ファイル", len(files))
