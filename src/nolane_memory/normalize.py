from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _normalize(value: Any) -> Any:
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {str(k): _normalize(value[k]) for k in sorted(value, key=lambda x: str(x))}
    if isinstance(value, (set, frozenset)):
        return sorted((_normalize(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")))
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, float):
        if value == 0.0:
            return 0.0
        return value
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_normalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def chain_root(previous_root: str, event: Any) -> str:
    h = hashlib.sha256()
    h.update(previous_root.encode("ascii"))
    h.update(b"\n")
    h.update(canonical_json(event).encode("utf-8"))
    return h.hexdigest()
