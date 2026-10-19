"""Integration-тесты CLI во временном каталоге."""

import json
import subprocess
import sys

GOOD = (
    '{"timestamp": "2026-10-01T10:00:00", "level": "INFO", "source": "auth", "message": "ok"}\n'
    '{"timestamp": "2026-10-01T10:05:00", "level": "ERROR", "source": "db", "message": "fail"}\n'
)
BAD = "{broken\n"


def run_cli(*args):
    """Запускает python -m streamstats с переданными аргументами."""
    return subprocess.run(
        [sys.executable, "-m", "streamstats", *args],
        cwd="src",
        capture_output=True,
        text=True,
        check=False,
    )

def test_csv_report(tmp_path):
    file_1 = tmp_path / "1.jsonl"
    report = tmp_path / "report.csv"
    file_1.write_text(GOOD, encoding="utf-8")

    result = run_cli("analyze", str(file_1), "--format", "jsonl", "--output", str(report))

    assert result.returncode == 0
    text = report.read_text(encoding="utf-8")
    assert "metric,key,value" in text
    assert "total_events,,2" in text
    assert "top_error_sources,db,1" in text


def test_empty_file(tmp_path):
    file_1 = tmp_path / "empty.jsonl"
    report = tmp_path / "report.json"
    file_1.write_text("", encoding="utf-8")

    result = run_cli("analyze", str(file_1), "--format", "jsonl", "--output", str(report))

    assert result.returncode == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["total_events"] == 0
    assert data["first_timestamp"] is None


def test_first_and_last_timestamp(tmp_path):
    file_1 = tmp_path / "1.jsonl"
    file_2 = tmp_path / "2.jsonl"
    report = tmp_path / "report.json"
    file_1.write_text(GOOD, encoding="utf-8")
    file_2.write_text(
        '{"timestamp": "2026-09-30T08:00:00", "level": "INFO", "source": "api", "message": "start"}\n',
        encoding="utf-8",
    )

    result = run_cli("analyze", str(file_1), str(file_2),
                     "--format", "jsonl", "--output", str(report))

    assert result.returncode == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["first_timestamp"] == "2026-09-30T08:00:00"
    assert data["last_timestamp"] == "2026-10-01T10:05:00"


def test_unicode(tmp_path):
    file_1 = tmp_path / "1.jsonl"
    report = tmp_path / "report.json"
    file_1.write_text(
        '{"timestamp": "2026-10-01T10:00:00", "level": "ERROR", "source": "сервис", "message": "Ошибка"}\n',
        encoding="utf-8",
    )

    result = run_cli("analyze", str(file_1), "--format", "jsonl", "--output", str(report))

    assert result.returncode == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["by_source"]["сервис"] == 1


def test_broken_csv_line_stops(tmp_path):
    file_1 = tmp_path / "1.csv"
    report = tmp_path / "report.json"
    file_1.write_text(
        "timestamp,level,source,message\nnot-a-date,INFO,auth,ok\n",
        encoding="utf-8",
    )

    result = run_cli("analyze", str(file_1), "--format", "csv", "--output", str(report))

    assert result.returncode == 2
    assert not report.exists()


def test_unsupported_format(tmp_path):
    file_1 = tmp_path / "1.jsonl"
    file_1.write_text(GOOD, encoding="utf-8")

    result = run_cli("analyze", str(file_1), "--format", "xml",
                     "--output", str(tmp_path / "report.json"))

    assert result.returncode == 2


def test_missing_file(tmp_path):
    result = run_cli("analyze", str(tmp_path / "nope.jsonl"), "--format", "jsonl",
                     "--output", str(tmp_path / "report.json"))

    assert result.returncode == 2