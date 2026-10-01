import json
from pathlib import Path

import pytest

from src.core.gate_engine import GateStateEngine, GateTransitionException
from src.cryptography.canonicalizer import canonicalize


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "master-reference-1251254.json"


def to_g12():
    e = GateStateEngine("ATK")
    for i in range(1, 13):
        e.transition_to(
            f"G{i}", "validator",
            human_authorisation=(i == 10),
            receipt_provided=(i == 12),
        )
    return e


def test_atk01_gate_skip_is_blocked_and_state_unchanged():
    e = GateStateEngine("ATK-01")
    with pytest.raises(GateTransitionException):
        e.transition_to("G10", "ATTACKER")
    assert e.get_current_gate() == "G0"
    assert e.state_history == []


def test_atk02_retrograde_transition_is_blocked():
    e = GateStateEngine("ATK-02")
    e.transition_to("G1", "DAEMON")
    e.transition_to("G2", "DAEMON")
    with pytest.raises(GateTransitionException):
        e.transition_to("G1", "ATTACKER")
    assert e.get_current_gate() == "G2"


def test_atk03_g10_spoof_is_blocked():
    e = GateStateEngine("ATK-03")
    for i in range(1, 10):
        e.transition_to(f"G{i}", "DAEMON")
    with pytest.raises(GateTransitionException):
        e.transition_to("G10", "ATTACKER", human_authorisation=False)
    assert e.get_current_gate() == "G9"


def test_atk04_nonfinite_payload_is_rejected():
    for value in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            canonicalize({"value": value})


def test_atk04_key_order_does_not_change_deterministic_encoding():
    a = {"z": 1, "a": {"b": 2, "a": 3}}
    b = {"a": {"a": 3, "b": 2}, "z": 1}
    assert canonicalize(a) == canonicalize(b)


def test_atk05_g13_unsigned_unverified_ingress_is_blocked():
    e = to_g12()
    with pytest.raises(GateTransitionException):
        e.transition_to("G13", "ATTACKER", evidence_provided=False)
    assert e.get_current_gate() == "G12"


def test_g14_g15_g16_cannot_be_forged():
    e = to_g12()
    e.transition_to("G13", "SOURCE", evidence_provided=True)

    with pytest.raises(GateTransitionException):
        e.transition_to("G14", "ATTACKER", authenticity_checked=False)

    e.transition_to("G14", "VALIDATOR", authenticity_checked=True)

    with pytest.raises(GateTransitionException):
        e.transition_to("G15", "ATTACKER", reconciled=False)

    e.transition_to("G15", "RECONCILER", reconciled=True)

    with pytest.raises(GateTransitionException):
        e.transition_to("G16", "ATTACKER",
                        evidence_provided=True,
                        authenticity_checked=True,
                        reconciled=False)

    assert e.get_current_gate() == "G15"


def test_failed_attacks_do_not_mutate_history():
    e = GateStateEngine("ATK-HISTORY")
    with pytest.raises(GateTransitionException):
        e.transition_to("G10", "ATTACKER")
    assert e.state_history == []


def test_master_status_remains_external_not_asserted():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert cfg["operationalStatus"]["externalLegalStatus"] == "NOT_ASSERTED"
    assert cfg["operationalStatus"]["primaryEvidence"] == "PENDING"
