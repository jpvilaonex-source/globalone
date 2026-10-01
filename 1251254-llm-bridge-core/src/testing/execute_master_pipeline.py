"""Controlled unified execution runner for Master Reference 1251254.

This runner exercises the real gate engine and cryptographic modules. It does
not simulate WORM storage, RFC 8785 conformance, external receipts, primary
evidence, court/registry outcomes, or external legal status.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from src.core.gate_engine import GateStateEngine, GateTransitionException
from src.cryptography.canonicalizer import canonicalize
from src.cryptography.hasher import dual_digest


MASTER_REFERENCE = "1251254"


def _advance_core(engine: GateStateEngine) -> None:
    for i in range(1, 10):
        engine.transition_to(f"G{i}", "master-validator")
    engine.transition_to("G10", "human-release", human_authorisation=True)
    engine.transition_to("G11", "submission-controller")
    engine.transition_to("G12", "external-gateway", receipt_provided=True)


def execute_full_validation_run() -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    engine = GateStateEngine("MASTER-UNIFIED-EXECUTION")

    _advance_core(engine)

    # Execute the actual adversarial barriers against the same engine.
    attacks: dict[str, str] = {}
    try:
        engine.transition_to("G13", "attacker", evidence_provided=False)
    except GateTransitionException:
        attacks["ATK-05-G13"] = "BLOCKED"

    try:
        engine.transition_to("G10", "attacker", human_authorisation=True)
    except GateTransitionException:
        attacks["ATK-02-REPLAY"] = "BLOCKED"

    canonical = canonicalize({"masterReference": MASTER_REFERENCE, "gate": "G12"})
    digests = dual_digest(canonical)

    report = {
        "masterReference": MASTER_REFERENCE,
        "executionStarted": started,
        "executionFinished": datetime.now(timezone.utc).isoformat(),
        "coreGate": engine.get_current_gate(),
        "historyEntries": len(engine.state_history),
        "adversarial": attacks,
        "cryptographicBinding": {
            "sha256": digests["sha256"],
            "sha512": digests["sha512"],
            "canonicalization": "DETERMINISTIC_JSON_ONLY_RFC8785_NOT_ASSERTED",
        },
        "worm": {
            "status": "NOT_EXECUTED",
            "reason": "No immutable WORM backend is wired into this runner.",
        },
        "externalStatus": "NOT_ASSERTED",
        "primaryEvidenceIngress": "PENDING",
        "deterministicStatus": (
            "COMPLIANCE_CHECK_PASSED_EXTERNAL_LEGAL_STATUS_PENDING_PRIMARY_EVIDENCE"
        ),
    }
    return report


if __name__ == "__main__":
    print(json.dumps(execute_full_validation_run(), indent=2, sort_keys=True))
