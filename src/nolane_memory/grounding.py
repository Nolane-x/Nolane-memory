from __future__ import annotations

import json
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Iterable

from .errors import (
    ActionArgumentMismatch,
    MemoryGroundingIncomplete,
    MemoryIntegrityError,
    MemoryScopeBlocked,
)
from .normalize import digest
from .runtime import MemoryRuntime as _BaseMemoryRuntime
from .types import Dependency, MemoryUseFence, RecallFrame


class GroundingCompleteness(str, Enum):
    """Bounded evidence levels for consequence-side dependency completeness.

    These levels describe how a consequence atom was bound to memory provenance. They
    are not truth/authority scores and must not be silently upgraded by a model.
    """

    UNKNOWN = "G0_UNKNOWN"
    MODEL_PROPOSED = "G1_MODEL_PROPOSED"
    AUDITED_BOUNDED = "G2_AUDITED_BOUNDED"
    STRUCTURED_BOUND = "G3_STRUCTURED_BOUND"
    DETERMINISTIC_CLOSED = "G4_DETERMINISTIC_CLOSED"


@dataclass(frozen=True)
class ConsequenceAtomGrounding:
    """A compact projection from one structured consequence atom to persisted memory.

    It deliberately carries identifiers plus a value digest, not a caller-supplied
    dependency list. At strong use, the runtime reloads the canonical persisted source
    frame and derives the dependency set itself.
    """

    atom_path: str
    value_digest: str
    source_frame_id: str
    source_role_id: str
    source_representation_id: str
    source_field: str
    completeness: str = GroundingCompleteness.STRUCTURED_BOUND.value


def _json_pointer_get(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise MemoryIntegrityError(f"invalid consequence atom JSON pointer: {pointer!r}")
    current = value
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise MemoryGroundingIncomplete(f"required consequence atom {pointer!r} is absent")
            current = current[token]
        elif isinstance(current, list):
            if token == "-":
                raise MemoryIntegrityError("'-' is not a readable JSON Pointer index")
            try:
                index = int(token)
            except ValueError as exc:
                raise MemoryIntegrityError(f"non-integer list index in JSON pointer: {token!r}") from exc
            if index < 0 or index >= len(current):
                raise MemoryGroundingIncomplete(f"required consequence atom {pointer!r} is absent")
            current = current[index]
        else:
            raise MemoryGroundingIncomplete(f"required consequence atom {pointer!r} is absent")
    return current


def _frame_from_storage(runtime: _BaseMemoryRuntime, frame_id: str) -> dict[str, Any]:
    row = runtime.db.execute(
        "SELECT domain_id,principal,frame_json FROM frames WHERE frame_id=?", (frame_id,)
    ).fetchone()
    if row is None:
        raise MemoryIntegrityError(f"grounding source frame {frame_id!r} is unavailable")
    data = json.loads(row["frame_json"])
    if data.get("frame_id") != frame_id:
        raise MemoryIntegrityError("persisted grounding frame identity mismatch")
    if data.get("domain_id") != row["domain_id"] or data.get("principal") != row["principal"]:
        raise MemoryIntegrityError("persisted grounding frame envelope mismatch")
    return data


def _grounding_fragment(data: dict[str, Any], grounding: ConsequenceAtomGrounding) -> dict[str, Any]:
    matches = [
        fragment
        for fragment in data.get("fragments", [])
        if fragment.get("role_id") == grounding.source_role_id
        and fragment.get("representation_id") == grounding.source_representation_id
    ]
    if len(matches) != 1:
        raise MemoryIntegrityError(
            "grounding source role/representation is absent or ambiguous in persisted frame"
        )
    return matches[0]


def _source_value(fragment: dict[str, Any], source_field: str) -> Any:
    payload = fragment.get("payload")
    if not isinstance(payload, dict) or source_field not in payload:
        raise MemoryIntegrityError(
            f"grounding source field {source_field!r} is absent from persisted fragment"
        )
    return payload[source_field]


class MemoryRuntime(_BaseMemoryRuntime):
    """v0.6.3 runtime plus opt-in G3 structured consequence grounding.

    The ordinary v0.6.3 `issue_use_fence` behavior is preserved when no consequence
    groundings are supplied. Grounded use extends the existing fence dependency set from
    canonical persisted source frames; it does not create a second truth/dependency store.
    """

    def ground_consequence_atom(
        self,
        frame: RecallFrame,
        *,
        role_id: str,
        source_field: str,
        atom_path: str,
    ) -> ConsequenceAtomGrounding:
        # Creation itself is only allowed from a currently valid frame. A stale source
        # cannot be laundered into a fresh-looking grounding projection.
        self.validate_dependencies(frame.domain_id, frame.dependencies)
        data = _frame_from_storage(self, frame.frame_id)
        if data["domain_id"] != frame.domain_id or data["principal"] != frame.principal:
            raise MemoryIntegrityError("grounding frame object differs from persisted envelope")

        object_matches = [
            fragment
            for fragment in frame.fragments
            if fragment.role_id == role_id
        ]
        if len(object_matches) != 1:
            raise MemoryIntegrityError("grounding role is absent or ambiguous in source frame")
        object_fragment = object_matches[0]

        probe = ConsequenceAtomGrounding(
            atom_path=atom_path,
            value_digest="",
            source_frame_id=frame.frame_id,
            source_role_id=role_id,
            source_representation_id=object_fragment.representation_id,
            source_field=source_field,
        )
        persisted_fragment = _grounding_fragment(data, probe)
        persisted_value = _source_value(persisted_fragment, source_field)
        object_payload = object_fragment.payload
        if not isinstance(object_payload, dict) or source_field not in object_payload:
            raise MemoryIntegrityError("source field is absent from supplied frame object")
        if digest(object_payload[source_field]) != digest(persisted_value):
            raise MemoryIntegrityError("supplied frame fragment differs from persisted source value")

        return ConsequenceAtomGrounding(
            atom_path=atom_path,
            value_digest=digest(persisted_value),
            source_frame_id=frame.frame_id,
            source_role_id=role_id,
            source_representation_id=object_fragment.representation_id,
            source_field=source_field,
        )

    def _close_consequence_groundings(
        self,
        frame: RecallFrame,
        *,
        principal: str,
        payload: Any,
        consequence_groundings: Iterable[ConsequenceAtomGrounding],
        required_grounding_paths: Iterable[str],
    ) -> list[Dependency]:
        groundings = list(consequence_groundings)
        required = set(required_grounding_paths)
        by_path: dict[str, ConsequenceAtomGrounding] = {}
        for grounding in groundings:
            if not isinstance(grounding, ConsequenceAtomGrounding):
                raise MemoryIntegrityError("unrecognized consequence grounding projection")
            if grounding.completeness != GroundingCompleteness.STRUCTURED_BOUND.value:
                raise MemoryGroundingIncomplete(
                    "strong structured use requires G3_STRUCTURED_BOUND grounding"
                )
            prior = by_path.get(grounding.atom_path)
            if prior is not None and prior != grounding:
                raise MemoryIntegrityError(
                    f"conflicting groundings for consequence atom {grounding.atom_path!r}"
                )
            by_path[grounding.atom_path] = grounding

        missing = sorted(required - set(by_path))
        if missing:
            raise MemoryGroundingIncomplete(
                "required consequence atoms lack structured memory grounding: " + ", ".join(missing)
            )

        merged: dict[tuple[str, str], Dependency] = {
            (dep.dep_class, dep.dep_key): dep for dep in frame.dependencies
        }
        for grounding in by_path.values():
            data = _frame_from_storage(self, grounding.source_frame_id)
            if data["domain_id"] != frame.domain_id:
                raise MemoryIntegrityError("cross-domain grounding requires an explicit governed import")
            if data["principal"] != principal:
                raise MemoryScopeBlocked("grounding source frame belongs to a different principal")

            fragment = _grounding_fragment(data, grounding)
            persisted_value = _source_value(fragment, grounding.source_field)
            if digest(persisted_value) != grounding.value_digest:
                raise MemoryIntegrityError("grounding source value digest no longer matches persisted frame")
            emitted_value = _json_pointer_get(payload, grounding.atom_path)
            if digest(emitted_value) != grounding.value_digest:
                raise ActionArgumentMismatch(
                    f"consequence atom {grounding.atom_path!r} differs from grounded memory value"
                )

            source_dependencies = [Dependency(**raw) for raw in data.get("dependencies", [])]
            # This is the E1 semantic step: reverse-grounded provenance joins the strong
            # consequence read-set, and its currentness is tested before a fence exists.
            self.validate_dependencies(frame.domain_id, source_dependencies)
            for dep in source_dependencies:
                key = (dep.dep_class, dep.dep_key)
                prior = merged.get(key)
                if prior is not None and prior.generation != dep.generation:
                    # Both source and current frame were individually validated against the
                    # current generation, so a disagreement here is an integrity failure.
                    raise MemoryIntegrityError(
                        f"incompatible dependency generations for {dep.dep_class}:{dep.dep_key}"
                    )
                merged[key] = dep

        return sorted(merged.values(), key=lambda dep: (dep.dep_class, dep.dep_key))

    def issue_use_fence(
        self,
        frame: RecallFrame,
        *,
        principal: str,
        sink: str,
        payload: Any,
        expires_at=None,
        consequence_groundings: Iterable[ConsequenceAtomGrounding] | None = None,
        required_grounding_paths: Iterable[str] | None = None,
    ) -> MemoryUseFence:
        groundings = list(consequence_groundings or [])
        required = set(required_grounding_paths or set())
        if not groundings and not required:
            return super().issue_use_fence(
                frame,
                principal=principal,
                sink=sink,
                payload=payload,
                expires_at=expires_at,
            )

        if principal != frame.principal:
            raise MemoryScopeBlocked("grounded consequence principal differs from frame principal")
        closed_dependencies = self._close_consequence_groundings(
            frame,
            principal=principal,
            payload=payload,
            consequence_groundings=groundings,
            required_grounding_paths=required,
        )
        closed_frame = replace(frame, dependencies=closed_dependencies)
        # The existing v0.6.3 fence remains the sole use-time owner. Its persisted
        # dependencies_json now contains the closed forward+reverse semantic read-set, so
        # mutation after issuance is caught again at consume_use_fence().
        return super().issue_use_fence(
            closed_frame,
            principal=principal,
            sink=sink,
            payload=payload,
            expires_at=expires_at,
        )
