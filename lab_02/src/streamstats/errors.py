"""Исключения пакета streamstats."""


class StreamStatsError(Exception):
    """Базовая ошибка stream_stats."""


class UnsupportedFormatError(StreamStatsError):
    """Неподдерживаемый формат."""


class InvalidEventError(StreamStatsError):
    """Неверное событие."""


class InvalidTimestampError(StreamStatsError):
    """Неверная временная метка."""


class CLIConfigError(StreamStatsError):
    """Ошибка конфигурации CLI."""
