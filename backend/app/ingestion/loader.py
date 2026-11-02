"""Reads CSV and JSON dataset files into a list of raw row dictionaries."""

import csv
import io
import json
from typing import Any

from app.core.errors import IngestionError


def parse_upload(filename: str, content: bytes, max_rows: int) -> tuple[str, list[dict[str, Any]]]:
    """Return (source_type, rows). Raises IngestionError for unsupported or malformed files."""
    name = (filename or "").lower()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestionError("The file must be UTF-8 encoded.") from exc

    if name.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or "text" not in [f.strip().lower() for f in reader.fieldnames]:
            raise IngestionError("CSV files must include a 'text' column.")
        rows = [{(k or "").strip().lower(): v for k, v in row.items()} for row in reader]
        source_type = "csv"
    elif name.endswith(".json"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise IngestionError("The JSON file could not be parsed.") from exc
        rows = data.get("records") if isinstance(data, dict) else data
        if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
            raise IngestionError("JSON files must contain a list of records (or {\"records\": [...]}).")
        rows = [{str(k).strip().lower(): v for k, v in r.items()} for r in rows]
        source_type = "json"
    else:
        raise IngestionError("Only .csv and .json files are supported.")

    if not rows:
        raise IngestionError("The file contains no records.")
    if len(rows) > max_rows:
        raise IngestionError(f"The file has {len(rows)} rows; the limit is {max_rows}.")
    return source_type, rows
