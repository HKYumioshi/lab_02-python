# streamstats

Потоковый анализатор файлов: читает события из CSV и JSONL и создаёт статистический отчёт в JSON или CSV.

## Функционал

- Построчное чтение входных файлов (файл целиком в память не загружается).
- Поддержка CSV с заголовком и JSONL.
- Валидация обязательных полей события.
- Подсчёт:
  - общего числа событий;
  - количества событий каждого уровня;
  - количества событий каждого источника;
  - top-5 источников ошибок уровня `ERROR` / `CRITICAL`;
  - первой и последней временной метки.
- Объединение статистики нескольких файлов в один отчёт.
- Отчёт в JSON или CSV (формат определяется по расширению `--output`).
- Два режима обработки ошибочных строк: остановка или пропуск (`--skip-invalid`).

## Модель события

| Поле | Требование |
|---|---|
| `timestamp` | дата и время в формате ISO 8601, например `2026-10-01T10:00:00` |
| `level` | одно из `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `source` | непустая строка |
| `message` | строка |

Пример JSONL (одно событие на строку):

```
{"timestamp": "2026-10-01T10:00:00", "level": "INFO", "source": "auth", "message": "User logged in"}
{"timestamp": "2026-10-01T10:05:12", "level": "ERROR", "source": "db", "message": "Connection timeout"}
```

Пример CSV (первая строка — заголовок):

```
timestamp,level,source,message
2026-10-01T10:00:00,INFO,auth,User logged in
2026-10-01T10:05:12,ERROR,db,Connection timeout
```

## Структура проекта

```
lab_02/
  pyproject.toml          настройки проекта, зависимостей, pytest, ruff
  README.md
  src/streamstats/
    __init__.py
    __main__.py           точка входа CLI, чтение файлов
    models.py             модель события и её валидация
    parsers.py            аргументы командной строки
    analysis.py           подсчёт и объединение статистики
    report.py             запись отчёта в JSON и CSV
    errors.py             исключения
  tests/
    test_parsers.py       unit-тесты чтения JSONL и CSV
    test_cli.py           integration-тесты CLI
```

## Установка

Требуется Python 3.13 или новее. Все команды выполняются из папки `lab_02`.

### Через Poetry

```
pip install poetry
poetry config virtualenvs.in-project true
poetry install
```

Команды запускаются через `poetry run`, например `poetry run python -m pytest`,
или после активации окружения (см. ниже) — без префикса.

### Через venv

```
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows (PowerShell)
source .venv/bin/activate         # Linux / macOS
pip install -e .
pip install pytest ruff
```

Выход из окружения — `deactivate`.

Если PowerShell пишет «выполнение сценариев отключено», один раз выполните:

```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Запуск

```
python -m streamstats analyze INPUT [INPUT ...] --format csv|jsonl --output REPORT.json
```

| Аргумент | Описание |
|---|---|
| `INPUT` | один или несколько входных файлов |
| `--format` | формат входных файлов: `csv` или `jsonl` |
| `--output` | файл отчёта: `.json` или `.csv` |
| `--skip-invalid` | пропускать ошибочные строки вместо остановки |

Примеры:

```
python -m streamstats --help
python -m streamstats analyze test_file.jsonl --format jsonl --output report.json
python -m streamstats analyze a.jsonl b.jsonl --format jsonl --output report.json
python -m streamstats analyze events.csv --format csv --output report.csv
python -m streamstats analyze test_file.jsonl --format jsonl --skip-invalid --output report.json
```

## Отчёт

Пример `report.json`:

```json
{
    "total_events": 2,
    "by_level": {"INFO": 1, "ERROR": 1},
    "by_source": {"auth": 1, "db": 1},
    "top_error_sources": [["db", 1]],
    "first_timestamp": "2026-10-01T10:00:00",
    "last_timestamp": "2026-10-01T10:05:12",
    "skipped_lines": 0
}
```

Тот же отчёт в CSV (`metric,key,value`):

```
metric,key,value
total_events,,2
by_level,INFO,1
by_level,ERROR,1
by_source,auth,1
by_source,db,1
top_error_sources,db,1
first_timestamp,,2026-10-01T10:00:00
last_timestamp,,2026-10-01T10:05:12
skipped_lines,,0
```

Статистика считается один раз; JSON и CSV строятся из одного и того же словаря отчёта (`build_report`).
Для пустого файла временные метки равны `null`.

## Ошибочные строки

- **По умолчанию** обработка останавливается, в stderr выводятся имя файла, номер строки и причина,
  программа завершается с кодом `2`. Отчёт не создаётся.
- **С `--skip-invalid`** строка пропускается, в лог пишется `WARNING` с файлом и номером строки,
  число пропущенных строк попадает в отчёт (`skipped_lines`).

Код `2` также возвращается при неподдерживаемом формате и при ошибке открытия файла (например, файл не найден).

## Исключения

Все ошибки программы наследуются от `StreamStatsError` (`errors.py`):

| Исключение | Когда возникает |
|---|---|
| `UnsupportedFormatError` | неподдерживаемый формат входа или отчёта |
| `InvalidEventError` | неверное событие (нет поля, неверный уровень, пустой источник, битый JSON) |
| `InvalidTimestampError` | временная метка не в формате ISO 8601 |
| `CLIConfigError` | ошибка конфигурации CLI |

На границе CLI (`main`) эти ошибки перехватываются и превращаются в понятное сообщение и код `2`.

## Проверка

```
python -m pytest
ruff check .
python -m streamstats --help
```