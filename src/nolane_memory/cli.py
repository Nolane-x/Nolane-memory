from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from .runtime import MemoryRuntime


def _dump(value) -> None:
    print(json.dumps(value, sort_keys=True, ensure_ascii=False))


def main() -> None:
    p = argparse.ArgumentParser(prog="nolane-memory")
    p.add_argument("--db", default="nolane-memory.db")
    sub = p.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init")
    init.add_argument("domain")
    init.add_argument("--writer-epoch", type=int, default=1)

    head = sub.add_parser("head")
    head.add_argument("domain")

    ev = sub.add_parser("capture")
    ev.add_argument("domain")
    ev.add_argument("source_event_identity")
    ev.add_argument("json_content")
    ev.add_argument("--principal", default="local")
    ev.add_argument("--operation-id", required=True)
    ev.add_argument("--expected-seq", type=int, required=True)
    ev.add_argument("--writer-epoch", type=int, default=1)

    sub.add_parser("status")

    debts = sub.add_parser("debts")
    debts.add_argument("domain")

    erase = sub.add_parser("erase")
    erase.add_argument("domain")
    erase.add_argument("evidence_id")
    erase.add_argument("--principal", required=True)
    erase.add_argument("--policy-ref", required=True)

    recover = sub.add_parser("recover")
    recover.add_argument("domain")
    recover.add_argument("--pin-id")
    recover.add_argument("--principal", required=True)

    sub.add_parser("lab")

    fuzz = sub.add_parser("fuzz")
    fuzz.add_argument("--seed", type=int, default=1)
    fuzz.add_argument("--cases", type=int, default=10_000)

    sub.add_parser("ownership")

    gate = sub.add_parser("release-gate")
    gate.add_argument("domain")
    gate.add_argument("--seed", type=int, default=603)
    gate.add_argument("--fuzz-cases", type=int, default=10_000)
    gate.add_argument("--differential-cases", type=int, default=128)

    args = p.parse_args()
    rt = MemoryRuntime(args.db)
    try:
        if args.cmd == "init":
            rt.create_domain(args.domain, writer_epoch=args.writer_epoch)
            _dump({"ok": True, "domain": args.domain})
        elif args.cmd == "head":
            _dump(asdict(rt.head(args.domain)))
        elif args.cmd == "capture":
            receipt = rt.capture_evidence(
                domain_id=args.domain, operation_id=args.operation_id, expected_seq=args.expected_seq,
                writer_epoch=args.writer_epoch, source_event_identity=args.source_event_identity,
                content=json.loads(args.json_content), principal=args.principal,
            )
            _dump(asdict(receipt))
        elif args.cmd == "status":
            _dump(rt.k5_profile_status())
        elif args.cmd == "debts":
            _dump([asdict(x) for x in rt.list_open_semantic_debts(args.domain)])
        elif args.cmd == "erase":
            _dump(asdict(rt.erase_evidence(args.domain, args.evidence_id, principal=args.principal, policy_ref=args.policy_ref)))
        elif args.cmd == "recover":
            _dump(asdict(rt.assess_recovery(args.domain, pin_id=args.pin_id, principal=args.principal)))
        elif args.cmd == "lab":
            _dump(asdict(rt.run_preservation_lab()))
        elif args.cmd == "fuzz":
            _dump(asdict(rt.run_lifelong_fuzz(seed=args.seed, cases=args.cases)))
        elif args.cmd == "ownership":
            _dump(rt.audit_full_spec_ownership())
        elif args.cmd == "release-gate":
            _dump(asdict(rt.run_full_spec_release_gate(
                args.domain, seed=args.seed, fuzz_cases=args.fuzz_cases, differential_cases=args.differential_cases
            )))
    finally:
        rt.close()


if __name__ == "__main__":
    main()
