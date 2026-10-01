import json
from pathlib import Path

import pytest

from src.connectors.base import BaseConnector
from src.core.gate_engine import GateStateEngine, GateTransitionException
from src.cryptography.canonicalizer import canonicalize
from src.reconciliation.reconciliation_engine import reconcile

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "master-reference-1251254.json"


class TestConnector(BaseConnector):
    def authenticate_session(self) -> bool:
        return True

    def submit_payload(self, payload, release_gate_cleared):
        if not release_gate_cleared:
            raise PermissionError("G11 transmission blocked until G10 human release.")
        return {"transmitted": True}

    def fetch_primary_evidence(self, receipt_id):
        return {"receipt_id": receipt_id}


def test_replay_cannot_move_gate_backward_or_repeat_current_gate():
    e = GateStateEngine("REPLAY")
    e.transition_to("G1", "validator")
    with pytest.raises(GateTransitionException):
        e.transition_to("G1", "replayer")
    assert e.get_current_gate() == "G1"


def test_direct_public_state_mutation_is_not_exposed():
    e = GateStateEngine("TAMPER")
    with pytest.raises(AttributeError):
        e.current_gate_index = 10


def test_audit_history_is_snapshot_not_mutable_state():
    e = GateStateEngine("AUDIT")
    e.transition_to("G1", "validator")
    history = e.state_history
    with pytest.raises(AttributeError):
        history.append({"forged": True})
    event = history[0]
    event["newState"] = "G19"
    assert e.state_history[0]["newState"] == "G1"


def test_empty_actor_is_rejected():
    e = GateStateEngine("ACTOR")
    with pytest.raises(GateTransitionException):
        e.transition_to("G1", " ")


def test_connector_blocks_external_submission_without_g10_release():
    connector = TestConnector("CONN", "TEST")
    with pytest.raises(PermissionError):
        connector.submit_payload({"x": 1}, release_gate_cleared=False)
    assert connector.submit_payload({"x": 1}, release_gate_cleared=True)["transmitted"] is True


def test_reconciliation_detects_tampered_observation():
    expected = {"receipt": "R1", "amount": 100}
    observed = {"receipt": "R1", "amount": 101}
    result = reconcile(expected, observed)
    assert result.matched is False
    assert result.discrepancies == ("amount",)


def test_canonical_payload_tamper_changes_digest():
    import hashlib
    original = canonicalize({"amount": 100, "receipt": "R1"})
    tampered = canonicalize({"amount": 101, "receipt": "R1"})
    assert hashlib.sha256(original).hexdigest() != hashlib.sha256(tampered).hexdigest()
    assert hashlib.sha512(original).hexdigest() != hashlib.sha512(tampered).hexdigest()


def test_external_status_remains_not_asserted():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert cfg["operationalStatus"]["externalLegalStatus"] == "NOT_ASSERTED"
