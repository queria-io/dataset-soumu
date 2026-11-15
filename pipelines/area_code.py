"""統計に用いる標準地域コードの取得。

総務省の「統計に用いる標準地域コード」のページから、現行のコード一覧（全国の CSV）と
2007 年 4 月 2 日以降のコードの変更（廃置分合）の履歴（Excel）を取得し、dbt が読む
NDJSON にする。

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
from collections.abc import Iterable, Iterator
from pathlib import Path
from urllib.parse import urljoin

import xlrd

from shared.fetch import fetch, write_atomic

logger = logging.getLogger("pipelines")

INDEX_URL = "https://www.soumu.go.jp/toukei_toukatsu/index/seido/9-5.htm"
USER_AGENT = "queria-dataset-soumu (+https://queria.io/)"
OUT_DIR = Path("data/area_code")


def _clean(value: object) -> str | None:
    s = str(value or "").replace("　", " ").strip()
    return s or None


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


def parse_municipality(text: str) -> list[dict]:
    """現行のコード一覧の CSV を行の辞書にする。

    列: ken-code, sityouson-code, tiiki-code, ken-name, sityouson-name1（郡・振興局・政令市）,
    sityouson-name2（未使用）, sityouson-name3（市区町村）, yomigana
    """
    return [
        {
            "area_code": r["tiiki-code"],
            "pref_code": r["ken-code"],
            "pref_name": r["ken-name"],
            "district_name": _clean(r.get("sityouson-name1")),
            "municipality_name": _clean(r.get("sityouson-name3")),
            "yomigana": _clean(r.get("yomigana")),
            "is_prefecture": r["sityouson-code"] == "000",
        }
        for r in csv.DictReader(io.StringIO(text))
    ]


def split_code_name(cell: object) -> tuple[str | None, str | None]:
    """'309　飯野町' -> ('309', '飯野町')。空のセルは (None, None)。"""
    s = _clean(cell)
    if s is None:
        return None, None
    m = re.match(r"^(\d+)\s*(.*)$", s)
    return (m.group(1), m.group(2).strip() or None) if m else (None, s)


def _is_heading(cell: str | None) -> bool:
    """旧コードの欄にある、コードでもよみがなでもない見出し（「参考：支庁から…」など）か。"""
    return bool(cell) and re.match(r"[\d（(]", cell) is None


def _fill_down(rows: Iterable[list[str | None]]) -> Iterator[tuple]:
    """都道府県・改正事由・施行年月日は 1 つの改正の先頭行にだけあるので、下の行へ送る。

    旧コードの欄の見出しは、その下に並ぶ変更の改正事由にする。前の改正の事由を送らない。
    """
    pref = reason = date = None
    for c0, c1, c2, c3, c4 in rows:
        pref, date = c0 or pref, (c4[:10] if c4 else date)
        reason = c3 or (c1 if _is_heading(c1) else reason)
        yield pref, c1, c2, reason, date


def _cell_text(cell: xlrd.sheet.Cell, datemode: int) -> str | None:
    """日付は ISO 形式、整数の数値は小数点なしの文字列にする。"""
    if cell.ctype == xlrd.XL_CELL_DATE:
        return xlrd.xldate.xldate_as_datetime(cell.value, datemode).date().isoformat()
    if cell.ctype == xlrd.XL_CELL_NUMBER and cell.value == int(cell.value):
        return str(int(cell.value))
    return _clean(cell.value)


def parse_changes(rows: list[list[str | None]], pref_codes: dict[str, str]) -> list[dict]:
    """変更の履歴の表（見出し行より下）を 1 件 1 行の辞書にする。

    影響を受ける市区町村を 1 行ずつ並べ、各行の直後によみがなの行が続く。新コードの欄に
    数字がある行だけを取り出す。
    """
    records = [
        (pref, *split_code_name(old), *split_code_name(new), reason, date)
        for pref, old, new, reason, date in _fill_down(rows)
        if new and re.search(r"\d", new)
    ]
    unknown = sorted({r[0] or "" for r in records} - pref_codes.keys())
    if unknown:
        raise SystemExit(f"都道府県名をコードに変換できない: {unknown}")
    return [
        {
            "effective_date": date,
            "pref_code": pref_codes[pref],
            "pref_name": pref,
            "old_code": pref_codes[pref] + old_code if old_code else None,
            "old_name": old_name,
            "new_code": pref_codes[pref] + new_code if new_code else None,
            "new_name": new_name,
            "is_code_deleted": bool(new_name and new_name.startswith("削除")),
            "reason": reason,
        }
        for pref, old_code, old_name, new_code, new_name, reason, date in records
    ]


def _change_rows(content: bytes) -> list[list[str | None]]:
    book = xlrd.open_workbook(file_contents=content)
    sheet = book.sheet_by_index(0)
    rows = [
        [_cell_text(sheet.cell(i, j), book.datemode) for j in range(5)]
        for i in range(sheet.nrows)
    ]
    header = next((i for i, r in enumerate(rows) if r[0] == "都道府県"), None)
    if header is None:
        raise SystemExit("変更の履歴の Excel に見出し行（都道府県）が無い")
    return rows[header + 1 :]


def _write_ndjson(records: list[dict], path: Path) -> None:
    write_atomic(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))


def build(out_dir: Path = OUT_DIR) -> None:
    """コード一覧と変更の履歴を取得し、NDJSON にする。"""
    html = fetch(INDEX_URL, user_agent=USER_AGENT).decode("cp932", errors="replace")
    csv_url, xls_url = resolve_links(html)
    logger.info(f"  downloading {csv_url}")
    municipality = parse_municipality(
        fetch(csv_url, user_agent=USER_AGENT).decode("cp932")
    )
    logger.info(f"  downloading {xls_url}")
    pref_codes = {r["pref_name"]: r["pref_code"] for r in municipality if r["is_prefecture"]}
    changes = parse_changes(_change_rows(fetch(xls_url, user_agent=USER_AGENT)), pref_codes)

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_ndjson(municipality, out_dir / "municipality.ndjson")
    _write_ndjson(changes, out_dir / "municipality_change.ndjson")
    logger.info(f"  municipality={len(municipality)} rows, municipality_change={len(changes)} rows")
