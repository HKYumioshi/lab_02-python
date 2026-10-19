"""Unit-тесты парсеров JSONL и CSV."""

import pytest

from src.streamstats.__main__ import (
    run_parse_events_csv,
    run_parse_events_csv_skipping_lines,
    run_parse_events_jsonl,
    run_parse_events_jsonl_skipping_lines,
)
from src.streamstats.errors import InvalidEventError

JSONL_GOOD = (
    '{"timestamp": "2026-10-01T10:00:00", "level": "INFO", "source": "auth", "message": "ok"}\n'
    '{"timestamp": "2026-10-01T10:05:00", "level": "ERROR", "source": "db", "message": "fail"}\n'
)
CSV_GOOD = (
    "timestamp,level,source,message\n"
    "2026-10-01T10:00:00,INFO,auth,ok\n"
    "2026-10-01T10:05:00,ERROR,db,fail\n"
)


def write(tmp_path, name, text):
    """Создаёт файл во временном каталоге и возвращает путь к нему."""
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_jsonl_parser(tmp_path):
    events = run_parse_events_jsonl(write(tmp_path, "a.jsonl", JSONL_GOOD))
    assert len(events) == 2
    assert events[1].level == "ERROR"
    assert events[1].source == "db"


def test_csv_parser(tmp_path):
    events = run_parse_events_csv(write(tmp_path, "a.csv", CSV_GOOD))
    assert len(events) == 2
    assert events[0].source == "auth"
    assert events[1].message == "fail"


def test_empty_jsonl(tmp_path):
    assert run_parse_events_jsonl(write(tmp_path, "e.jsonl", "")) == []


def test_empty_csv(tmp_path):
    assert run_parse_events_csv(write(tmp_path, "e.csv", "")) == []


def test_broken_jsonl_line_raises(tmp_path):
    path = write(tmp_path, "b.jsonl", JSONL_GOOD + "{broken\n")
    with pytest.raises(InvalidEventError, match="строка 3"):
        run_parse_events_jsonl(path)


def test_broken_csv_line_raises(tmp_path):
    path = write(tmp_path, "b.csv", CSV_GOOD + "not-a-date,INFO,auth,x\n")
    with pytest.raises(InvalidEventError, match="строка 4"):
        run_parse_events_csv(path)


def test_broken_jsonl_line_skipped(tmp_path):
    text = JSONL_GOOD + "{broken\n" + '{"timestamp": "2026-10-01T10:00:00", "level": "BAD", "source": "x", "message": ""}\n'
    events, skipped = run_parse_events_jsonl_skipping_lines(write(tmp_path, "b.jsonl", text))
    assert len(events) == 2
    assert skipped == 2


def test_broken_csv_line_skipped(tmp_path):
    text = CSV_GOOD + "not-a-date,INFO,auth,x\n2026-10-01T10:00:00,INFO,,x\n"
    events, skipped = run_parse_events_csv_skipping_lines(write(tmp_path, "b.csv", text))
    assert len(events) == 2
    assert skipped == 2


def test_unicode(tmp_path):
    jsonl = '{"timestamp": "2026-10-01T10:00:00", "level": "INFO", "source": "сервис", "message": "Привет, 世界 🙂"}\n'
    csv_text = "timestamp,level,source,message\n2026-10-01T10:00:00,INFO,сервис,\"Привет, 世界 🙂\"\n"
    jsonl_events = run_parse_events_jsonl(write(tmp_path, "u.jsonl", jsonl))
    csv_events = run_parse_events_csv(write(tmp_path, "u.csv", csv_text))
    assert jsonl_events[0].source == "сервис"
    assert csv_events[0].message == "Привет, 世界 🙂"
