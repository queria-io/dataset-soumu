"""統計に用いる標準地域コードの取得。

総務省の「統計に用いる標準地域コード」のページから、現行のコード一覧（全国の CSV）と
2007 年 4 月 2 日以降のコードの変更（廃置分合）の履歴（Excel）を取得し、dbt が読む
NDJSON にする。CSV は行を列名のまま、Excel はセルの値を文字にして 1 行ずつ書く。
列名の付け替えや、改正の先頭行にだけある値を下の行へ送る処理は dbt の stg で行う。

ファイルの ID（main_content/000323625.csv など）は改正のたびに変わるので、URL は
ページから求める。

出典: 総務省 統計に用いる標準地域コード
https://www.soumu.go.jp/toukei_toukatsu/index/seido/9-5.htm
"""

import csv
import io
import json
import logging
import re
from pathlib import Path
from urllib.parse import urljoin

import xlrd

from shared.fetch import fetch, fetch_file, write_atomic

logger = logging.getLogger("pipelines")

INDEX_URL = "https://www.soumu.go.jp/toukei_toukatsu/index/seido/9-5.htm"
USER_AGENT = "queria-dataset-soumu (+https://queria.io/)"
OUT_DIR = Path("data/area_code")


def resolve_links(html: str) -> tuple[str, str]:
    """ページに 1 件ずつ載る CSV と Excel の URL を返す。"""
    hrefs = [urljoin(INDEX_URL, h) for h in re.findall(r'href="([^"]+)"', html)]
    csvs = [h for h in hrefs if h.lower().endswith(".csv")]
    xlss = [h for h in hrefs if h.lower().endswith((".xls", ".xlsx"))]
    if len(csvs) != 1 or len(xlss) != 1:
        raise SystemExit(
            f"unexpected file links on {INDEX_URL} (csv={len(csvs)}, excel={len(xlss)})"
        )
    return csvs[0], xlss[0]


def csv_rows(content: bytes, sha256: str) -> list[dict]:
    """コード一覧の CSV の行を、列名のまま辞書にする。source_row は見出しを 1 行目とした行番号。"""
    return [
        {"source_sha256": sha256, "source_row": i, **row}
        for i, row in enumerate(csv.DictReader(io.StringIO(content.decode("cp932"))), 2)
    ]


def _cell_text(cell: xlrd.sheet.Cell, datemode: int) -> str | None:
    """日付は ISO 形式、整数の数値は小数点なしの文字列にする。空のセルは None。"""
    if cell.ctype == xlrd.XL_CELL_DATE:
        return xlrd.xldate.xldate_as_datetime(cell.value, datemode).date().isoformat()
    if cell.ctype == xlrd.XL_CELL_NUMBER and cell.value == int(cell.value):
        return str(int(cell.value))
    return str(cell.value) if cell.value != "" else None


def excel_rows(content: bytes, sha256: str) -> list[dict]:
    """変更の履歴の Excel の最初のシートの行を、A〜E 列の値の辞書にする。行番号は 1 始まり。"""
    book = xlrd.open_workbook(file_contents=content)
    sheet = book.sheet_by_index(0)
    return [
        {
            "source_sha256": sha256,
            "source_sheet": sheet.name,
            "source_row": i + 1,
            **{f"col_{j + 1}": _cell_text(sheet.cell(i, j), book.datemode) for j in range(5)},
        }
        for i in range(sheet.nrows)
    ]


def _write_ndjson(records: list[dict], path: Path) -> None:
    write_atomic(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))


def build(out_dir: Path = OUT_DIR) -> None:
    """コード一覧と変更の履歴を取得し、取得したファイルの一覧と行を NDJSON にする。

    前回の一覧の行があり手元にファイルがあれば条件付き GET を送り、変わっていなければ取得しない。
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    record = out_dir / "source_file.ndjson"
    previous = (
        {row["url"]: row for row in map(json.loads, record.read_text(encoding="utf-8").splitlines())}
        if record.exists()
        else {}
    )
    html = fetch(INDEX_URL, user_agent=USER_AGENT).decode("cp932", errors="replace")

    def get(url: str) -> tuple[dict, bytes]:
        logger.info(f"  downloading {url}")
        path = out_dir / url.rsplit("/", 1)[1]
        row = fetch_file(url, path, previous=previous.get(url), user_agent=USER_AGENT)
        return {**row, "page_url": INDEX_URL}, path.read_bytes()

    (csv_file, csv_content), (xls_file, xls_content) = map(get, resolve_links(html))
    municipality = csv_rows(csv_content, csv_file["sha256"])
    changes = excel_rows(xls_content, xls_file["sha256"])

    _write_ndjson([csv_file, xls_file], record)
    _write_ndjson(municipality, out_dir / "municipality.ndjson")
    _write_ndjson(changes, out_dir / "municipality_change.ndjson")
    logger.info(f"  municipality={len(municipality)} rows, municipality_change={len(changes)} rows")
