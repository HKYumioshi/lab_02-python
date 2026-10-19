"""Модель события и её валидация."""

from dataclasses import dataclass
from datetime import datetime

from streamstats.errors import InvalidEventError, InvalidTimestampError

LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
REQUIRED_FIELDS = ("timestamp", "level", "source", "message")


@dataclass(frozen=True, slots=True)
class Event:
    """Одно событие лога."""

    timestamp: datetime
    level: str
    source: str
    message: str


def parse_event(record: dict) -> Event:
    """Проверяет обязательные поля записи и создаёт из неё Event."""
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        raise InvalidEventError(f"Missing required fields: {', '.join(missing)}")

    raw_timestamp = record["timestamp"]
    if not isinstance(raw_timestamp, str):
        raise InvalidTimestampError("Timestamp must be a string")
    try:
        timestamp = datetime.fromisoformat(raw_timestamp)
    except ValueError as exc:
        raise InvalidTimestampError("Timestamp not in ISO8601 format") from exc

    level = record["level"]
    if not isinstance(level, str) or level not in LEVELS:
        raise InvalidEventError(f"Invalid level: {level!r}")

    source = record["source"]
    if not isinstance(source, str) or not source.strip():
        raise InvalidEventError("Source must be a non-empty string")

    message = record["message"]
    if not isinstance(message, str):
        raise InvalidEventError("Message must be a string")

    return Event(timestamp=timestamp, level=level, source=source, message=message)
