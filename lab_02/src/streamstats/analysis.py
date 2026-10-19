"""Подсчёт статистики по событиям."""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from streamstats.models import Event

ERROR_LEVELS = frozenset({"ERROR", "CRITICAL"})

@dataclass(slots=True)
class Stats:
    """Накопленная статистика по событиям."""

    total_events: int = 0
    by_level: Counter[str] = field(default_factory=Counter)
    by_source: Counter[str] = field(default_factory=Counter)
    errors_by_source: Counter[str] = field(default_factory=Counter)
    first_timestamp: datetime | None = None
    last_timestamp: datetime | None = None
    skipped_lines: int = 0

def add_event(stats: Stats, event: Event) -> Stats:
    """Учитывает одно событие в статистике."""
    stats.total_events += 1
    stats.by_level[event.level] += 1
    stats.by_source[event.source] += 1
    if event.level in ERROR_LEVELS:
        stats.errors_by_source[event.source] += 1
    if not stats.first_timestamp or stats.first_timestamp > event.timestamp:
        stats.first_timestamp = event.timestamp
    if not stats.last_timestamp or stats.last_timestamp < event.timestamp:
        stats.last_timestamp = event.timestamp

    return stats

def merge_two_stats(stats_1: Stats, stats_2: Stats) -> Stats:
    """Добавляет статистику stats_2 к stats_1 и возвращает stats_1."""
    stats_1.total_events += stats_2.total_events
    stats_1.by_level.update(stats_2.by_level)
    stats_1.by_source.update(stats_2.by_source)
    stats_1.errors_by_source.update(stats_2.errors_by_source)
    stats_1.skipped_lines += stats_2.skipped_lines
    for ts in (stats_2.first_timestamp, stats_2.last_timestamp):
        if ts is None:
            continue
        if not stats_1.first_timestamp or ts < stats_1.first_timestamp:
            stats_1.first_timestamp = ts
        if not stats_1.last_timestamp or ts > stats_1.last_timestamp:
            stats_1.last_timestamp = ts
    return stats_1

def add_skipped_lines(stats: Stats, skipped_lines: int) -> Stats:
    """Добавляет число пропущенных строк в статистику."""
    stats.skipped_lines += skipped_lines
    return stats

def analyze_events(events: list[Event]) -> Stats:
    """Считает статистику по списку событий."""
    stats = Stats()
    for event in events:
        add_event(stats, event)
    return stats
