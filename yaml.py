from __future__ import annotations

from typing import Any, Dict, List


def _coerce_scalar(value: str) -> Any:
    if value.isdigit():
        try:
            return int(value)
        except ValueError:
            pass
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value


def safe_load(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    current_list_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            if current_list_key is None:
                raise ValueError("List item found without preceding key")
            data.setdefault(current_list_key, []).append(_coerce_scalar(line[2:].strip()))
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                data[key] = []
                current_list_key = key
            else:
                data[key] = _coerce_scalar(value)
                current_list_key = None
        else:
            raise ValueError(f"Invalid line in YAML: {line}")
    return data


__all__ = ["safe_load"]
