"""把「11」「2026.8.10」「20097」解成层数、日期或日程 id。"""

import re
import datetime
from typing import TypedDict

_DATE = re.compile(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})")


class RangeRow(TypedDict):
    id: str
    begin: str
    end: str
    title: str


def parse_date(text: str) -> datetime.date | None:
    found = _DATE.search(text)
    if found is None:
        return None
    year = int(found.group(1))
    month = int(found.group(2))
    day = int(found.group(3))
    try:
        return datetime.date(year, month, day)
    except ValueError:
        return None


def parse_abyss_args(text: str) -> tuple[int, datetime.date | None, str]:
    """返回 (层数, 日期, 日程id)。层数缺省 12。"""
    when = parse_date(text)
    rest = _DATE.sub(" ", text)
    floor = 12
    schedule_id = ""
    for num in re.findall(r"\d+", rest):
        value = int(num)
        if 1 <= value <= 12:
            floor = value
        elif value >= 10000:
            schedule_id = num
    return floor, when, schedule_id


def parse_schedule_args(text: str) -> tuple[datetime.date | None, str]:
    """剧诗 / 幽境：日期或日程 id。两者都有时以 id 为准。"""
    when = parse_date(text)
    rest = _DATE.sub(" ", text)
    schedule_id = ""
    for num in re.findall(r"\d+", rest):
        if int(num) >= 1:
            schedule_id = num
    return when, schedule_id


def _day(text: str) -> datetime.date:
    return datetime.datetime.strptime(text[:10], "%Y-%m-%d").date()


def covering_id(rows: list[RangeRow], day: datetime.date) -> str:
    """日期落在哪一期。多期重叠时取开始更晚的。"""
    found = ""
    found_begin = ""
    for row in rows:
        if _day(row["begin"]) <= day <= _day(row["end"]) and row["begin"] >= found_begin:
            found = row["id"]
            found_begin = row["begin"]
    return found


def period_shift(command: str, text: str) -> int:
    """上期=-1，下期=1。相对今天所在的当期，或相对 text 里的日期。"""
    blob = f"{command}\n{text}"
    if "下期" in blob:
        return 1
    if "上期" in blob:
        return -1
    return 0


def neighbor_id(rows: list[RangeRow], day: datetime.date, shift: int) -> str:
    """当期是覆盖这一天的一期；没有则用已经开过的最近一期。再按开始时间走 shift 步。"""
    ordered = sorted(rows, key=lambda row: (row["begin"], row["id"]))
    if not ordered:
        return ""
    current = covering_id(rows, day)
    if not current:
        opened = [row for row in ordered if _day(row["begin"]) <= day]
        current = opened[-1]["id"] if opened else ""
    if not current:
        return ""
    index = 0
    found = False
    for pos, row in enumerate(ordered):
        if row["id"] == current:
            index = pos
            found = True
            break
    if not found:
        return ""
    target = index + shift
    if target < 0 or target >= len(ordered):
        return ""
    return ordered[target]["id"]


def choose_id(
    rows: list[RangeRow],
    *,
    today: datetime.date,
    when: datetime.date | None,
    pinned: str,
    shift: int,
) -> str:
    if pinned:
        for row in rows:
            if row["id"] == pinned:
                return pinned
        return ""
    anchor = when if when is not None else today
    if shift:
        return neighbor_id(rows, anchor, shift)
    if when is not None:
        return covering_id(rows, when)
    return neighbor_id(rows, today, 0)


def format_ranges(kind: str, rows: list[RangeRow]) -> str:
    ordered = sorted(rows, key=lambda row: row["begin"])
    lines = [f"【{kind}日程对照】text 可写日期、id、上期或下期。上期/下期相对今天的当期。"]
    for row in ordered:
        title = f" {row['title']}" if row["title"] else ""
        lines.append(f"{row['id']} {row['begin'][:10]}~{row['end'][:10]}{title}")
    return "\n".join(lines)
