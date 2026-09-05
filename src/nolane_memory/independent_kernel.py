from __future__ import annotations

"""A deliberately independent pure-Python semantic challenger.

This module does not import the SQLite runtime, its normalizer, or its type system.
It exists to make hidden semantic assumptions observable through differential tests.
"""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _norm(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {str(k): _norm(value[k]) for k in sorted(value, key=lambda x: str(x))}
    if isinstance(value, (set, frozenset)):
        return sorted((_norm(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")))
    if isinstance(value, (list, tuple)):
        return [_norm(v) for v in value]
    if isinstance(value, float) and value == 0.0:
        return 0.0
    return value


def independent_canonical_json(value: Any) -> str:
    return json.dumps(_norm(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def independent_digest(value: Any) -> str:
    return hashlib.sha256(independent_canonical_json(value).encode("utf-8")).hexdigest()


class IndependentSemanticKernel:
    """Small semantic state machine used as an independent conformance oracle."""

    EXACT_STATES = {"PRESERVED_EXACT", "PRESERVED_NORMALIZED"}

    def __init__(self):
        self.query_families: dict[str, dict[str, Any]] = {}
        self.evidence_by_sid: dict[str, dict[str, Any]] = {}
        self.evidence_names: dict[str, str] = {}
        self.regions: dict[str, str] = {}
        self.representations: dict[str, dict[str, Any]] = {}
        self.claims: dict[str, dict[str, Any]] = {}

    def register_query_family(self, family_id: str, dimensions: set[str], revision: int = 1) -> None:
        current = self.query_families.get(family_id)
        if current is None:
            if revision != 1:
                raise ValueError("first revision must be 1")
        else:
            if revision != current["revision"] + 1:
                raise ValueError("query family revision must be contiguous")
        self.query_families[family_id] = {"revision": int(revision), "dimensions": set(dimensions)}

    def capture_evidence(
        self, name: str, source_event_identity: str, content: Any, *, delivery_id: str,
        roots: list[str] | None = None, common_mode_group: str | None = None,
    ) -> None:
        c_digest = independent_digest(content)
        roots_norm = sorted(set(roots or [f"source:{source_event_identity}"]))
        current = self.evidence_by_sid.get(source_event_identity)
        if current is not None:
            if current["content_digest"] != c_digest or current["roots"] != roots_norm:
                raise ValueError("semantic evidence identity collision")
            current["deliveries"].add(delivery_id)
        else:
            self.evidence_by_sid[source_event_identity] = {
                "content_digest": c_digest,
                "roots": roots_norm,
                "common_modes": sorted({common_mode_group or root for root in roots_norm}),
                "deliveries": {delivery_id},
                "revoked": False,
            }
        self.evidence_names[name] = source_event_identity

    def revoke_evidence(self, name: str) -> None:
        sid = self.evidence_names[name]
        self.evidence_by_sid[sid]["revoked"] = True

    def create_region(self, name: str, semantic_key: str) -> None:
        if name in self.regions and self.regions[name] != semantic_key:
            raise ValueError("region identity collision")
        self.regions[name] = semantic_key

    def add_representation(
        self, name: str, *, region_name: str, kind: str, payload: Any,
        loss: dict[str, str], recoverable: set[str], source_representation_names: list[str] | None = None,
    ) -> None:
        if region_name not in self.regions:
            raise KeyError(region_name)
        self.representations[name] = {
            "region_name": region_name,
            "kind": kind,
            "payload_digest": independent_digest(payload),
            "loss": {str(k): str(v) for k, v in loss.items()},
            "recoverable": set(recoverable),
            "sources": list(source_representation_names or []),
            "invalidated": False,
        }

    def invalidate_representation(self, name: str) -> None:
        self.representations[name]["invalidated"] = True

    def create_claim(self, logical_id: str, support_paths: list[list[str]]) -> None:
        self.claims[logical_id] = {"support_paths": [list(path) for path in support_paths]}

    def claim_supported(self, logical_id: str) -> bool:
        claim = self.claims[logical_id]
        for path in claim["support_paths"]:
            if path and all(not self.evidence_by_sid[self.evidence_names[name]]["revoked"] for name in path):
                return True
        return False

    def _source_can_supply(self, representation_name: str, dimension: str, seen: set[str] | None = None) -> bool:
        seen = set() if seen is None else seen
        if representation_name in seen:
            return False
        seen.add(representation_name)
        row = self.representations[representation_name]
        if row["invalidated"]:
            return False
        if row["loss"].get(dimension, "UNKNOWN") in self.EXACT_STATES:
            return True
        if dimension not in row["recoverable"]:
            return False
        return any(self._source_can_supply(src, dimension, set(seen)) for src in row["sources"])

    def answerability(self, representation_name: str, family_id: str) -> str:
        row = self.representations[representation_name]
        if row["invalidated"]:
            return "UNSUPPORTED"
        required = set(self.query_families[family_id]["dimensions"])
        loss = row["loss"]
        if all(loss.get(dim) in self.EXACT_STATES for dim in required):
            return "EXACT"
        unknown = any(loss.get(dim, "UNKNOWN") == "UNKNOWN" for dim in required)
        available = {dim for dim in required if loss.get(dim) in self.EXACT_STATES}
        if required.issubset(available | row["recoverable"]):
            # Recoverability is valid only when a source route really supplies the missing dimensions.
            missing = required - available
            if all(any(self._source_can_supply(src, dim) for src in row["sources"]) for dim in missing):
                return "REHYDRATABLE"
        if unknown:
            return "UNKNOWN"
        return "UNSUPPORTED"

    def snapshot(self) -> dict[str, Any]:
        evidence = []
        for sid in sorted(self.evidence_by_sid):
            row = self.evidence_by_sid[sid]
            evidence.append((
                sid, row["content_digest"], row["revoked"], tuple(row["roots"]),
                tuple(row["common_modes"]), len(row["deliveries"]),
            ))
        representations = []
        for name in sorted(self.representations):
            row = self.representations[name]
            representations.append((
                name, self.regions[row["region_name"]], row["kind"], row["payload_digest"],
                tuple(sorted(row["loss"].items())), tuple(sorted(row["recoverable"])), row["invalidated"],
            ))
        return {
            "evidence": evidence,
            "regions": sorted(self.regions.values()),
            "representations": representations,
            "claims": sorted((logical_id, self.claim_supported(logical_id)) for logical_id in self.claims),
            "query_families": sorted(
                (fid, row["revision"], tuple(sorted(row["dimensions"]))) for fid, row in self.query_families.items()
            ),
        }
