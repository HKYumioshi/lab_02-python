"""Парсер аргументов командной строки."""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Создаёт парсер CLI с подкомандой analyze."""
    parser = argparse.ArgumentParser(
        prog = "streamstats",
        description = "Пакет, читающий события из CSV и JSONL и создающий статистический отчет"
    )
    subparsers = parser.add_subparsers(dest = "command", required = True)
    analyze_parser = subparsers.add_parser(
        "analyze",
        help = "Проанализировать входные данные"
    )
    analyze_parser.add_argument(
        "INPUT",
        help = "входные данные (один или несколько файлов)",
        nargs='+',
    )
    analyze_parser.add_argument(
        "--format",
        dest = "format",
        required = True,
        metavar = "csv|jsonl",
        help = "Формат входных данных (csv|jsonl)"
    )
    analyze_parser.add_argument(
        "--output",
        dest = "output",
        required = True,
        metavar = "REPORT.json|csv",
        help = "Файл, в который будет загружен результат анализа"
    )
    analyze_parser.add_argument(
        "--skip-invalid",
        action = "store_true",
        required = False,
        help = "Пропустить строки с ошибками"
    )
    return parser
