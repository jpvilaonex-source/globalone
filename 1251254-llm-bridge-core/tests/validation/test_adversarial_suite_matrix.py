import pytest

from src.core.gate_engine import GateStateEngine, GateTransitionException
from src.cryptography.canonicalizer import canonicalize


def advance_to_g9():
    e = GateStateEngine("FORMAL-ATK")
    for i in range(1, 10):
        e.transition_to(f"G{i}", "validator")
    return e


def advance_to_g12():
    e = advance_to_g9()
    e.transition_to("G10", "human", human_authorisation=True)
    e.transition_to("G11", "connector")
    e.transition_to("G12", "gateway", receipt_provided=True)
    return e


@pytest.mark.parametrize("target", [f"G{i}" for i in range(1, 20)])
def test_atk01_all_non_next_gate_jumps_are_blocked(target):
    e = GateStateEngine("ATK-01")
    if target == "G1":
        e.transition_to(target, "validator")
        return
    with pytest.raises(GateTransitionException):
        e.transition_to(target, "attacker")
    assert e.get_current_gate() == "G0"


def test_atk02_retrograde_and_replay_are_blocked():
    e = advance_to_g9()
    with pytest.raises(GateTransitionException):
        e.transition_to("G8", "attacker")
    e.transition_to("G10", "human", human_authorisation=True)
    with pytest.raises(GateTransitionException):
        e.transition_to("G10", "replayer", human_authorisation=True)
    assert e.get_current_gate() == "G10"


def test_atk03_g10_spoof_is_blocked():
    e = advance_to_g9()
    with pytest.raises(GateTransitionException):
        e.transition_to("G10", "attacker", human_authorisation=False)
    assert e.get_current_gate() == "G9"


def test_atk04_nonfinite_values_are_rejected():
    for value in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            canonicalize({"value": value})


def test_atk05_evidence_ingress_requires_primary_evidence():
    e = advance_to_g12()
    with pytest.raises(GateTransitionException):
        e.transition_to("G13", "attacker", evidence_provided=False)
    assert e.get_current_gate() == "G12"


def test_atk05_g14_requires_authenticity():
    e = advance_to_g12()
    e.transition_to("G13", "source", evidence_provided=True)
    with pytest.raises(GateTransitionException):
        e.transition_to("G14", "attacker", authenticity_checked=False)
    assert e.get_current_gate() == "G13"


def test_atk05_g15_requires_reconciliation():
    e = advance_to_g12()
    e.transition_to("G13", "source", evidence_provided=True)
    e.transition_to("G14", "validator", authenticity_checked=True)
    with pytest.raises(GateTransitionException):
        e.transition_to("G15", "attacker", reconciled=False)
    assert e.get_current_gate() == "G14"


def test_atk05_g16_requires_all_three_conditions():
    e = advance_to_g12()
    e.transition_to("G13", "source", evidence_provided=True)
    e.transition_to("G14", "validator", authenticity_checked=True)
    e.transition_to("G15", "reconciler", reconciled=True)
    for kwargs in (
        {"evidence_provided": False, "authenticity_checked": True, "reconciled": True},
        {"evidence_provided": True, "authenticity_checked": False, "reconciled": True},
        {"evidence_provided": True, "authenticity_checked": True, "reconciled": False},
    ):
        with pytest.raises(GateTransitionException):
            e.transition_to("G16", "attacker", **kwargs)
    assert e.get_current_gate() == "G15"


def test_failed_attack_does_not_append_history():
    e = GateStateEngine("ATK-HISTORY")
    before = e.state_history
    with pytest.raises(GateTransitionException):
        e.transition_to("G10", "attacker")
    assert e.state_history == before
