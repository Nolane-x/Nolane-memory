#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict, is_dataclass
from typing import Any

from nolane_memory import MemoryRuntime, RecallRole


class BridgeMethodNotAllowed(RuntimeError):
    pass


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, set):
        return sorted(_jsonable(v) for v in value)
    if hasattr(value, "value") and isinstance(getattr(value, "value"), (str, int, float, bool, type(None))):
        return value.value
    return value


def _domain_exists(rt: MemoryRuntime, domain: str) -> bool:
    return bool(rt.list_authority_domain_revisions(domain))


def _stable_operation_id(params: dict[str, Any]) -> str:
    material = {
        "domain": params["domain"],
        "principal": params["principal"],
        "source_event_identity": params["source_event_identity"],
        "content": params["content"],
        "transport_channel": params.get("transport_channel", "deepseek-harness"),
        "external_identity": params.get("external_identity"),
        "source_authority_class": params.get("source_authority_class", "UNSPECIFIED"),
        "common_mode_group": params.get("common_mode_group"),
    }
    blob = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "dsh_capture_" + hashlib.sha256(blob).hexdigest()[:32]


def _require_domain(rt: MemoryRuntime, params: dict[str, Any]) -> str:
    domain = str(params.get("domain") or "")
    if not domain:
        raise ValueError("domain is required")
    if not _domain_exists(rt, domain):
        if params.get("auto_create_domain"):
            rt.create_domain(domain)
        else:
            raise KeyError(domain)
    return domain


def dispatch(request: dict[str, Any]) -> Any:
    method = str(request.get("method") or "")
    params = dict(request.get("params") or {})
    db = str(params.get("db") or "")
    if not db:
        raise ValueError("db is required")
    rt = MemoryRuntime(db)
    try:
        if method == "status":
            domain = str(params.get("domain") or "")
            exists = bool(domain) and _domain_exists(rt, domain)
            result: dict[str, Any] = {
                "domain_exists": exists,
                "profile": rt.k5_profile_status(),
            }
            if exists:
                result["head"] = asdict(rt.head(domain))
                result["integrity"] = rt.verify_integrity(domain)
            return result

        if method == "capture":
            domain = _require_domain(rt, params)
            principal = str(params.get("principal") or "")
            source_event_identity = str(params.get("source_event_identity") or "")
            if not principal or not source_event_identity:
                raise ValueError("principal and source_event_identity are required")
            head = rt.head(domain)
            fences = rt.list_writer_fence_revisions(domain)
            if not fences:
                raise RuntimeError("writer fence history missing")
            receipt = rt.capture_evidence(
                domain_id=domain,
                operation_id=str(params.get("operation_id") or _stable_operation_id(params)),
                expected_seq=head.sequence,
                writer_epoch=fences[-1].writer_epoch,
                source_event_identity=source_event_identity,
                content=params.get("content"),
                principal=principal,
                transport_channel=str(params.get("transport_channel") or "deepseek-harness"),
                external_identity=(str(params["external_identity"]) if params.get("external_identity") is not None else None),
                source_authority_class=str(params.get("source_authority_class") or "UNSPECIFIED"),
                common_mode_group=(str(params["common_mode_group"]) if params.get("common_mode_group") is not None else None),
                binder_procedure="deepseek-harness-bridge-v1",
            )
            return receipt

        if method == "recall":
            domain = _require_domain(rt, params)
            principal = str(params.get("principal") or "")
            if not principal:
                raise ValueError("principal is required")
            raw_roles = params.get("roles")
            if not isinstance(raw_roles, list) or not raw_roles:
                raise ValueError("roles must be a non-empty list")
            roles = [RecallRole(**dict(role)) for role in raw_roles]
            frame = rt.compile_recall(
                domain,
                principal,
                roles,
                int(params.get("token_budget", 4096)),
                page_fault_budget=int(params.get("page_fault_budget", 32)),
                compatibility_profile=dict(params.get("compatibility_profile") or {}),
                safety_critical_dimensions=set(params.get("safety_critical_dimensions") or []),
            )
            return frame

        if method == "verify":
            domain = _require_domain(rt, params)
            clocks = asdict(rt.audit_no_two_writable_clocks(domain))
            clocks["ok"] = bool(clocks.get("passed"))
            return {
                "integrity": rt.verify_integrity(domain),
                "no_two_writable_clocks": clocks,
                "ownership": rt.audit_full_spec_ownership(),
            }

        if method == "release_gate":
            domain = _require_domain(rt, params)
            return rt.run_full_spec_release_gate(
                domain,
                seed=int(params.get("seed", 603)),
                fuzz_cases=int(params.get("fuzz_cases", 10_000)),
                differential_cases=int(params.get("differential_cases", 128)),
            )

        raise BridgeMethodNotAllowed(f"method {method!r} is not allowed")
    finally:
        rt.close()


def main() -> int:
    line = sys.stdin.readline()
    if not line:
        return 2
    request_id: Any = None
    try:
        request = json.loads(line)
        request_id = request.get("id")
        result = _jsonable(dispatch(request))
        response = {"id": request_id, "ok": True, "result": result}
    except Exception as exc:
        response = {
            "id": request_id,
            "ok": False,
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
    sys.stdout.write(json.dumps(response, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
