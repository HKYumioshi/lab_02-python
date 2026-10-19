"""Точка входа CLI: python -m streamstats analyze ..."""

import csv
import json
import logging
import sys

from streamstats.analysis import (
    Stats,
    add_skipped_lines,
    analyze_events,
    merge_two_stats,
)
from streamstats.errors import (
    InvalidEventError,
    StreamStatsError,
    UnsupportedFormatError,
    CLIConfigError
)
from streamstats.models import parse_event
from streamstats.parsers import build_parser
from streamstats.report import report_in_csv, report_in_json

logger = logging.getLogger("streamstats")


def run_parse_events_jsonl(path):
    """Читает JSONL-файл построчно и возвращает список событий.

    При первой ошибочной строке возбуждает InvalidEventError
    с именем файла и номером строки.
    """
    event_list = []
    with open(path, "r", encoding = "utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                raise InvalidEventError(f"{path}, строка {line_number}: {line} не является валидным JSON")
            if not isinstance(item, dict):
                raise InvalidEventError(f"{path}, строка {line_number}: ожидался JSON-объект")
            try:
                event_list.append(parse_event(item))
            except StreamStatsError as exc:
                raise InvalidEventError(f"{path}, строка {line_number}: {exc}") from exc
    return event_list

def run_parse_events_jsonl_skipping_lines(path):
    """Читает JSONL-файл построчно, пропуская ошибочные строки.

    Для каждой пропущенной строки пишет WARNING в лог.
    Возвращает кортеж (список событий, число пропущенных строк).
    """
    event_list = []
    skipped_lines = 0
    with open(path, "r", encoding = "utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                skipped_lines += 1
                logger.warning(f"{path}, строка {line_number}: {line} не является валидным JSON")
                continue
            if not isinstance(item, dict):
                skipped_lines += 1
                logger.warning(f"{path}, строка {line_number}: ожидался JSON-объект")
                continue
            try:
                event_list.append(parse_event(item))
            except StreamStatsError as exc:
                skipped_lines += 1
                logger.warning(f"{path}, строка {line_number}: {exc}")
                continue
    return (event_list, skipped_lines)

def run_parse_events_csv(path):
    """Читает CSV-файл с заголовком построчно и возвращает список событий.

    При первой ошибочной строке возбуждает InvalidEventError
    с именем файла и номером строки.
    """
    event_list = []
    with open(path, "r", encoding = "utf-8", newline = "") as file:
        reader = csv.DictReader(file)
        # строка 1 — заголовок, поэтому данные начинаются со строки 2
        for line_number, row in enumerate(reader, start=2):
            try:
                event_list.append(parse_event(row))
            except StreamStatsError as exc:
                raise InvalidEventError(f"{path}, строка {line_number}: {exc}") from exc
    return event_list

def run_parse_events_csv_skipping_lines(path):
    """Читает CSV-файл с заголовком построчно, пропуская ошибочные строки.

    Для каждой пропущенной строки пишет WARNING в лог.
    Возвращает кортеж (список событий, число пропущенных строк).
    """
    event_list = []
    skipped_lines = 0
    with open(path, "r", encoding = "utf-8", newline = "") as file:
        reader = csv.DictReader(file)
        for line_number, row in enumerate(reader, start=2):
            try:
                event_list.append(parse_event(row))
            except StreamStatsError as exc:
                skipped_lines += 1
                logger.warning(f"{path}, строка {line_number}: {exc}")
                continue
    return (event_list, skipped_lines)

def main(argv: list | None = None):
    """Разбирает аргументы командной строки, обрабатывает файлы и пишет отчёт.

    Возвращает код завершения: 0 при успехе, 2 при ошибке.
    """
    logging.basicConfig(format="%(levelname)s: %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.format == "jsonl":
            parsed_jsonl_files = []
            if args.skip_invalid:
                for item in args.INPUT:
                    parsed_jsonl_files.append(run_parse_events_jsonl_skipping_lines(item))
            else:
                for item in args.INPUT:
                    parsed_jsonl_files.append((run_parse_events_jsonl(item), 0))
            stats_list = []
            for item, skipped_lines in parsed_jsonl_files:
                stats = analyze_events(item)
                stats = add_skipped_lines(stats, skipped_lines)
                stats_list.append(stats)
            total_stats = Stats()
            for item in stats_list:
                total_stats = merge_two_stats(total_stats, item)
        elif args.format == "csv":
            parsed_csv_files = []
            if args.skip_invalid:
                for item in args.INPUT:
                    parsed_csv_files.append(run_parse_events_csv_skipping_lines(item))
            else:
                for item in args.INPUT:
                    parsed_csv_files.append((run_parse_events_csv(item), 0))
            stats_list = []
            for item, skipped_lines in parsed_csv_files:
                stats = analyze_events(item)
                stats = add_skipped_lines(stats, skipped_lines)
                stats_list.append(stats)
            total_stats = Stats()
            for item in stats_list:
                total_stats = merge_two_stats(total_stats, item)
        else:
            raise UnsupportedFormatError("Unsupported input file format")
        if args.output.endswith('.json'):
            report_in_json(total_stats, args.output)
        elif args.output.endswith('.csv'):
            report_in_csv(total_stats, args.output)
        else:
            raise UnsupportedFormatError("Unsupported output file format")
    except StreamStatsError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        raise CLIConfigError(f"Ошибка работы с файлом: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
