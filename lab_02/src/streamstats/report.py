"""Формирование отчёта в JSON и CSV."""

import csv
import json

from streamstats.analysis import Stats


def build_report(total_stats: Stats) -> dict:
    """Собирает данные отчёта в словарь (общий для JSON и CSV)."""
    first_timestamp = total_stats.first_timestamp
    last_timestamp = total_stats.last_timestamp
    return {
        "total_events": total_stats.total_events,
        "by_level": dict(total_stats.by_level),
        "by_source": dict(total_stats.by_source),
        "top_error_sources": total_stats.errors_by_source.most_common(5),
        "first_timestamp": first_timestamp.isoformat() if first_timestamp else None,
        "last_timestamp": last_timestamp.isoformat() if last_timestamp else None,
        "skipped_lines": total_stats.skipped_lines
    }

def report_in_json(total_stats: Stats, file_path: str) -> None:
    """Записывает отчёт в JSON-файл."""
    report = build_report(total_stats)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)


def report_in_csv(total_stats: Stats, file_path: str) -> None:
    """Записывает отчёт в CSV-файл со столбцами metric, key, value."""
    report = build_report(total_stats)
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "key", "value"])
        for metric, value in report.items():
            if isinstance(value, dict):
                for key, count in value.items():
                    writer.writerow([metric, key, count])
            elif isinstance(value, list):
                for key, count in value:
                    writer.writerow([metric, key, count])
            else:
                writer.writerow([metric, "", value])
