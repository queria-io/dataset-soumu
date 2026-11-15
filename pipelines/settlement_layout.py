"""市町村別決算状況調の Excel のセルから、見出し・団体の行を読む。

pipelines/municipal_settlement.py が Excel ごとに呼び、結果を raw_sheets・raw_columns・raw_rows にする。
年度によって列の並び・見出し・ファイルの分け方が違うので、表の見出しの行から列ごとの項目名を作る。
"""

import re
import unicodedata

PREFECTURES = (
    "北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 "
    "神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 "
    "大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 "
    "福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県"
).split()
SHORT_PREFECTURES = {
    re.sub(r"[都府県]$", "", p) if p != "北海道" else p: p for p in PREFECTURES
}

TABLES = ("概況", "歳入内訳", "目的別歳出内訳", "性質別歳出内訳", "地方債現在高等", "歳出内訳")


def normalize(value) -> str:
    """見出し・団体名の文字を NFKC にし、空白と改行を除く。"""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value)))



def cell(grid: list[list], r: int, c: int):
    return grid[r][c] if r < len(grid) and c < len(grid[r]) else None


def prefecture(text: str) -> str | None:
    return text if text in PREFECTURES else SHORT_PREFECTURES.get(text)


def as_code(value) -> str | None:
    text = normalize(value)
    return text.zfill(6) if re.fullmatch(r"\d{5,6}", text) else None


def as_number(value) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = normalize(value).replace(",", "").replace("△", "-").replace("▲", "-")
    try:
        return float(text)
    except ValueError:
        return None


def header_texts(grid: list[list], merged: dict, rows: range, cols: range) -> dict[tuple[int, int], str]:
    """見出しのセルの文字。結合セルは左上の文字を使う。

    結合していない空のセルは、この列の見出しがそれより下の行から始まり、左の列の見出しにも下の行に
    子の見出しがあるときに、左の列の文字を引き継ぐ（古い年度の Excel は、親の見出しを結合せずに
    左端の列だけに書いている）。子の見出しの無い左の列（「面積」など）は親ではないので引き継がない。
    """
    texts = {}
    for r in rows:
        for c in cols:
            r0, c0 = merged.get((r, c), (r, c))
            texts[r, c] = normalize(cell(grid, r0, c0))
    named = lambda r, c: bool(header_part(texts[r, c])[0])
    for r in rows:
        for c in cols:
            if (
                not texts[r, c]
                and (r, c) not in merged
                and c - 1 in cols
                and texts[r, c - 1]
                and not any(texts[r2, c] for r2 in rows if r2 < r)
                and any(named(r2, c) for r2 in rows if r2 > r)
                and any(named(r2, c - 1) for r2 in rows if r2 > r)
            ):
                texts[r, c] = texts[r, c - 1]
    return texts


UNIT = re.compile(r"\((人|%|km2|千円|円)\)")
# 見出しの番号（一・1・ア・(1)）と、列どうしの計算式の記号（(A)・(A)-(B)）
NUMBERING = re.compile(r"^(?:[一二三四五六七八九十]+|\d+|[ア-ン]|\([\dア-ン]+\)|\([A-Z]\)[-+()A-Z]*)$")
# 「一地方税」「1普通交付税」「(ア)給料」の番号。「一時借入金」の「一」は番号ではない
LEADING_NUMBER = re.compile(r"^(?:[一二三四五六七八九十]+(?!時)|\d+(?=[^\d.年月日])|\([\dア-ン]+\))")
# 「(平14.10.1現在)」「(平15.3.31)」の時点。括弧の無い「平12.10.1」は国勢調査人口の列の名前なので残す
AS_OF = re.compile(r"\(?[^()]*\d+\.\d+(?:\.\d+)?現在\)?|\([^()]*\d+\.\d+\.\d+\)")


def header_part(text: str) -> tuple[str, str | None]:
    """見出しのセル 1 つを、項目名の一部と単位に分ける。"""
    units = UNIT.findall(text)
    text = UNIT.sub("", text)
    text = AS_OF.sub("", text)
    if NUMBERING.match(text):
        return "", units[-1] if units else None
    return LEADING_NUMBER.sub("", text), units[-1] if units else None


FORMULA = re.compile(r"(?:\([A-Z]\)[-+]?)+$")
# 1 つの見出しが改行で 2 つのセルに分かれているときの、前のセルの終わりと次のセルの始まり
CONTINUED = re.compile(r"(?:^うち|を|越|及び|繰上|共済|長等)$")
CONTINUING = re.compile(r"^(?:の|に?対する|を除く|すべき|除く|\(翌年度|負担金$|事業負担金$|登載人口$)")


def join_parts(parts: list[str]) -> str:
    """見出しを親から順に「/」でつなぐ。2 つのセルに分かれた 1 つの見出しはそのままつなぐ。

    親の「地方税内訳」は「地方税」にする（古い年度は「内訳」を付けずに親の見出しを書いている）。
    """
    parts = [re.sub(r"(?<=.)内訳$", "", p) for p in parts[:-1]] + parts[-1:]
    item = parts[0]
    for previous, part in zip(parts, parts[1:]):
        item += part if CONTINUED.search(previous) or CONTINUING.match(part) else "/" + part
    return FORMULA.sub("", item)


Columns = dict[int, tuple[str, str | None]]


def attach_subsets(columns: Columns) -> Columns:
    """「うち〜」の列と「内訳」の下の列は、左にある列の内数なので、その列の項目名の下に置く。

    同じ「うち人件費」が普通建設事業費と災害復旧事業費の両方の右に、同じ「内訳/新規整備」が
    補助事業費と単独事業費の両方の右にあるので、親を付けないと区別できない。
    「左のうち/人件費」は左の列（経常収支比率）の「うち人件費」にする。
    内数の列に単位が無いときは、左の列の単位を使う（「職員数(人)」の右の「うち一般職員」）。
    """
    result, base, base_unit = {}, None, None
    for c, (item, unit) in columns.items():
        leaf = item.rsplit("/", 1)[-1]
        if base and item.startswith("左のうち/"):
            item = f"{base}/うち{item.removeprefix('左のうち/')}"
        elif base and leaf.startswith("うち"):
            item = f"{base}/{leaf}"
        elif base and "/内訳/" in item:
            item = f"{base}/{item.split('/内訳/', 1)[1]}"
        else:
            base, base_unit = item, unit
        result[c] = (item, unit or base_unit)
    return result


def sheet_title(grid: list[list], until: int) -> str:
    return "".join(normalize(v) for row in grid[:until] for v in row if v is not None)


def merged_columns(grid: list[list], merged: dict, rows: range, cols: list[int]) -> Columns:
    """見出しのセルを結合している Excel（平成19年度から）の、列ごとの項目名と単位。"""
    texts = header_texts(grid, merged, rows, cols)
    columns = {}
    for c in cols:
        parts, unit = [], None
        for r in rows:
            part, part_unit = header_part(texts[r, c])
            unit = part_unit or unit
            if part and part not in parts:
                parts.append(part)
        if parts:
            columns[c] = (join_parts(parts), unit)
    return columns


MARKER = re.compile(r"^(?:([一二三四五六七八九十]+)(?!時)|(\d+)(?=[^\d.年月日])|\((\d+)\)|\(([ア-ン])\))")


def level(text: str) -> int | None:
    """見出しの番号の階層。一 → 1、1 → 2、(1) → 3、(ア) → 4。番号が無ければ None。"""
    match = MARKER.match(text)
    return next(i for i, group in enumerate(match.groups(), 1) if group) if match else None


def numbered_columns(grid: list[list], merged: dict, rows: range, cols: list[int]) -> Columns:
    """見出しのセルを結合していない Excel（平成18年度まで）の、列ごとの項目名と単位。

    親の見出しは左端の列にだけ書かれ、1 つの見出しが改行で下のセルに続いていることがある。
    番号（一・1・(1)・(ア)）の付いたセルを見出しの始まり、番号の無い下のセルをその続きとみなし、
    番号の階層で親をたどる。番号の付いていない列（概況など）は見出しを並べる。
    """
    texts = header_texts(grid, merged, rows, cols)
    columns, stack = {}, []
    for c in cols:
        segments, unit = [], None
        for r in rows:
            text = normalize(cell(grid, r, c))
            part, part_unit = header_part(text)
            unit = part_unit or unit
            lvl = level(text)
            if part.endswith("内訳") and lvl is None:
                # 「国庫財源を伴うもの内訳」は左の親の見出しの繰り返し
                continue
            if lvl is None and segments and segments[0][0] is not None:
                segments[-1] = (segments[-1][0], segments[-1][1] + part)
            elif part or lvl is not None:
                segments.append((lvl, part))
        if not segments:
            continue
        if segments[0][0] is None:
            parts = [p for r in rows if (p := header_part(texts[r, c])[0])]
        else:
            stack = [s for s in stack if s[0] < segments[0][0]] + segments
            parts = [p for _, p in stack if p]
        if parts:
            columns[c] = (join_parts(list(dict.fromkeys(parts))), unit)
    return columns


# 国勢調査の年が入った見出し。年を外した項目名と、値の元になった国勢調査の年（西暦）にする
ERA = {"令": 2018, "令和": 2018, "平": 1988, "平成": 1988}
CENSUS = (
    # 国勢調査人口/令2.10.1
    (re.compile(r"^(国勢調査人口)/(令|平)(\d+)\.10\.1$"), lambda m: (m[1], ERA[m[2]] + int(m[3]))),
    # 国勢調査人口/対平27増減率（前回の国勢調査からの増減率。値は 5 年後の国勢調査のもの）
    (re.compile(r"^(国勢調査人口)/対(平)(\d+)増減率$"), lambda m: (f"{m[1]}/増減率", ERA[m[2]] + int(m[3]) + 5)),
    # 産業構造(令和2年国調)/第1次。元号の無いものは平成
    (re.compile(r"^(産業構造)\((令和|平成)?(\d+)年国調\)(/.+)$"), lambda m: (m[1] + m[4], ERA[m[2] or "平成"] + int(m[3]))),
)


def item_name(heading: str) -> tuple[str, int | None]:
    """見出しから、年度をまたいで同じ名前になる項目名と国勢調査の年を作る。"""
    heading = heading.replace("補てん", "補塡")
    for pattern, convert in CENSUS:
        if m := pattern.match(heading):
            return convert(m)
    return heading, None


def parse(grid: list[list], merged: dict, file: dict, category: str | None) -> dict:
    """シート 1 つの見出しと行を読む。

    区分の書かれていないシート（概況その2）は前のファイルの区分（category）を使う。
    返すのは、シート（区分・表）と、列ごとの項目名・単位と、団体の行（都道府県・団体名・団体コード）。
    """
    header = next(
        r for r, row in enumerate(grid) if any(normalize(v) == "団体名" for v in row)
    )
    name_col = next(c for c, v in enumerate(grid[header]) if normalize(v) == "団体名")
    code_col = next(
        (c for c, v in enumerate(grid[header]) if normalize(v) == "団体コード"), None
    )
    first = next(
        r
        for r in range(header + 1, len(grid))
        if any(prefecture(normalize(v)) for v in grid[r])
        or (code_col is not None and as_code(cell(grid, r, code_col)))
    )
    # 古い年度は見出しが「団体名」の行より上から始まる
    top = header
    while top > 0 and (above := "".join(normalize(v) for v in grid[top - 1])) and not re.search(
        r"単位|都市別|町村別", above
    ):
        top -= 1
    title = sheet_title(grid, top)
    category = "都市" if "都市別" in title else "町村" if "町村別" in title else category
    # 概況その2 のシートには表の名前が無い
    table = next((name for name in TABLES if name in title), "概況")
    sheet_unit = "千円" if "千円" in title else None
    cols = [c for c in range(name_col + 1, max(len(row) for row in grid)) if c != code_col]
    # 表題や注記の結合セルではなく、見出しの行に結合セルがあるかで読み方を決める
    header_merged = any(top <= r < first for r, _ in merged)
    columns = (merged_columns if header_merged else numbered_columns)(
        grid, merged, range(top, first), cols
    )
    columns = {
        # 財政力指数は単位の無い指数
        c: (item, None if "財政力指数" in item else unit or sheet_unit)
        for c, (item, unit) in attach_subsets(columns).items()
    }

    entities, pref = [], None
    for r in range(first, len(grid)):
        texts = [normalize(v) for v in grid[r]]
        found = next((prefecture(t) for t in texts if prefecture(t)), None)
        name = normalize(cell(grid, r, name_col))
        code = as_code(cell(grid, r, code_col)) if code_col is not None else None
        if found and not code and (not name or prefecture(name)):
            pref = found
            continue
        if not name or "計" in name or name.startswith("(") or (code_col is not None and not code):
            continue
        # 注記の行（「2.平成20年4月1日以降の…」）は値を持たない
        if all(as_number(cell(grid, r, c)) is None for c in columns):
            continue
        entities.append((r, pref, name, code))

    return {
        "category": category,
        "sheet": (file["sha256"], file["fiscal_year"], category, table, top + 1, first + 1, name_col + 1, code_col + 1 if code_col is not None else None),
        "columns": [
            (file["sha256"], c + 1, heading, *item_name(heading), unit) for c, (heading, unit) in columns.items()
        ],
        "rows": [(file["sha256"], r + 1, pref, name, code) for r, pref, name, code in entities],
    }


# raw のテーブルの列。行番号・列番号は Excel と同じ 1 始まり
COLUMNS = {
    "sheets": {
        "source_sha256": "VARCHAR",
        "fiscal_year": "INTEGER",
        "entity_group": "VARCHAR",
        "section": "VARCHAR",
        "header_first_row": "INTEGER",
        "data_first_row": "INTEGER",
        "name_col": "INTEGER",
        "code_col": "INTEGER",
    },
    "columns": {
        "source_sha256": "VARCHAR",
        "col_no": "INTEGER",
        "heading": "VARCHAR",
        "item": "VARCHAR",
        "census_year": "INTEGER",
        "unit": "VARCHAR",
    },
    "rows": {
        "source_sha256": "VARCHAR",
        "source_row": "INTEGER",
        "pref_name": "VARCHAR",
        "entity_name": "VARCHAR",
        "lg_code": "VARCHAR",
    },
}

