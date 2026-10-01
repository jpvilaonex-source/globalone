import hashlib
import json
from pathlib import Path

import pytest

from src.core.gate_engine import GateStateEngine, GateTransitionException, VALID_GATES
from src.cryptography.hasher import dual_digest
from src.cryptography.canonicalizer import canonicalize

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "master-reference-1251254.json"

def test_master_configuration_invariants_are_locked():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert cfg["masterReference"] == "1251254"
    assert cfg["systemName"] == "LLM BRIDGE"
    assert cfg["architectureEngine"] == "UNIVERSAL 20-GATE EVIDENCE ENGINE"
    assert cfg["governingControlInvariants"] == {"noSelfAuthentication": True, "noFactElevation": True, "noSimulation": True, "noRetroactiveGateBypass": True}
    assert cfg["operationalStatus"]["externalLegalStatus"] == "NOT_ASSERTED"

def test_every_gate_exists_in_exact_master_order():
    assert VALID_GATES == [f"G{i}" for i in range(20)]

def test_complete_g0_to_g19_path_requires_each_control():
    engine = GateStateEngine("VALIDATION-COMPONENT-001")
    for i in range(1, 20):
        kwargs = {}
        if i == 10: kwargs["human_authorisation"] = True
        if i == 12: kwargs["receipt_provided"] = True
        if i == 13: kwargs["evidence_provided"] = True
        if i == 14: kwargs["authenticity_checked"] = True
        if i == 15: kwargs["reconciled"] = True
        if i == 16: kwargs.update(evidence_provided=True, authenticity_checked=True, reconciled=True)
        assert engine.transition_to(f"G{i}", "validation-runner", **kwargs) == f"G{i}"
    assert engine.get_current_gate() == "G19"
    assert len(engine.state_history) == 19

@pytest.mark.parametrize("target", ["G2", "G5", "G10", "G19"])
def test_no_gate_jump_or_retroactive_bypass(target):
    engine = GateStateEngine("VALIDATION-COMPONENT-002")
    with pytest.raises(GateTransitionException): engine.transition_to(target, "validation-runner")

def test_g10_cannot_be_released_without_human_authorisation():
    engine = GateStateEngine("VALIDATION-COMPONENT-003")
    for i in range(1, 10): engine.transition_to(f"G{i}", "validation-runner")
    with pytest.raises(GateTransitionException): engine.transition_to("G10", "automation")

def test_g12_requires_external_receipt():
    engine = GateStateEngine("VALIDATION-COMPONENT-004")
    for i in range(1, 12): engine.transition_to(f"G{i}", "validation-runner", human_authorisation=(i == 10))
    with pytest.raises(GateTransitionException): engine.transition_to("G12", "connector")

def test_g13_g14_g15_g16_are_individually_evidence_gated():
    engine = GateStateEngine("VALIDATION-COMPONENT-005")
    for i in range(1, 13): engine.transition_to(f"G{i}", "validation-runner", human_authorisation=(i == 10), receipt_provided=(i == 12))
    with pytest.raises(GateTransitionException): engine.transition_to("G13", "connector")
    engine.transition_to("G13", "evidence-source", evidence_provided=True)
    with pytest.raises(GateTransitionException): engine.transition_to("G14", "validator")
    engine.transition_to("G14", "validator", authenticity_checked=True)
    with pytest.raises(GateTransitionException): engine.transition_to("G15", "reconciler")
    engine.transition_to("G15", "reconciler", reconciled=True)
    with pytest.raises(GateTransitionException): engine.transition_to("G16", "verifier")
    assert engine.transition_to("G16", "verifier", evidence_provided=True, authenticity_checked=True, reconciled=True) == "G16"

def test_dual_hashes_match_independent_sha256_sha512():
    payload = b"1251254 validation payload"
    result = dual_digest(payload)
    assert result["sha256"] == hashlib.sha256(payload).hexdigest()
    assert result["sha512"] == hashlib.sha512(payload).hexdigest()
    assert len(result["sha256"]) == 64
    assert len(result["sha512"]) == 128

def test_empty_input_hash_vectors_are_test_vectors_only():
    result = dual_digest(b"")
    assert result["sha256"] == hashlib.sha256(b"").hexdigest()
    assert result["sha512"] == hashlib.sha512(b"").hexdigest()

def test_canonicalization_is_deterministic_and_rejects_nonfinite_numbers():
    left = {"b": 2, "a": "x", "nested": {"z": 1, "a": 0}}
    right = {"nested": {"a": 0, "z": 1}, "a": "x", "b": 2}
    assert canonicalize(left) == canonicalize(right)
    with pytest.raises(ValueError): canonicalize({"bad": float("nan")})
    with pytest.raises(ValueError): canonicalize({"bad": float("inf")})

def test_internal_state_does_not_claim_external_legal_effect():
    status = json.loads(CONFIG.read_text(encoding="utf-8"))["operationalStatus"]
    assert status["control"] == "BOUND"
    assert status["architecture"] == "ACTIVE"
    assert status["enforcement"] == "FULL"
    assert status["externalLegalStatus"] == "NOT_ASSERTED"
    assert status["primaryEvidence"] == "PENDING"