import threading
import pytest

from src.core.gate_engine import GateStateEngine, GateTransitionException
from src.reconciliation.reconciliation_engine import reconcile


def test_receipt_reuse_cannot_advance_without_new_gate_state():
    e = GateStateEngine("RECEIPT-REUSE")
    for i in range(1, 12):
        e.transition_to(f"G{i}", "validator", human_authorisation=(i == 10))
    with pytest.raises(GateTransitionException):
        e.transition_to("G12", "replayer", receipt_provided=False)
    e.transition_to("G12", "validator", receipt_provided=True)
    with pytest.raises(GateTransitionException):
        e.transition_to("G12", "replayer", receipt_provided=True)
    assert e.get_current_gate() == "G12"


def test_reconciliation_requires_exact_match():
    expected = {"receipt": "R-1", "status": "accepted", "amount": 100}
    observed = {"receipt": "R-1", "status": "accepted", "amount": 101}
    result = reconcile(expected, observed)
    assert not result.matched
    assert result.discrepancies == ("amount",)


def test_concurrent_single_step_attempts_cannot_both_advance():
    e = GateStateEngine("CONCURRENCY")
    outcomes = []
    lock = threading.Lock()

    def attempt():
        try:
            value = e.transition_to("G1", "worker")
            with lock:
                outcomes.append(("ok", value))
        except GateTransitionException:
            with lock:
                outcomes.append(("blocked", None))

    threads = [threading.Thread(target=attempt) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert e.get_current_gate() == "G1"
    assert sum(x[0] == "ok" for x in outcomes) == 1
    assert sum(x[0] == "blocked" for x in outcomes) == 7


def test_audit_store_rejects_replay_and_preserves_hash_chain():
    from src.core.persistence_controls import AppendOnlyAuditStore, PersistenceControlError
    import hashlib
    import json

    store = AppendOnlyAuditStore()

    def event_hash(previous, payload):
        raw = json.dumps(
            {"previousHash": previous, "payload": payload},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode()
        return hashlib.sha256(raw).hexdigest()

    first = {"action": "G1"}
    h1 = event_hash("GENESIS", first)
    store.append("IDEM-1", first, h1)

    with pytest.raises(PersistenceControlError):
        store.append("IDEM-1", first, h1)

    second = {"action": "G2"}
    h2 = event_hash(h1, second)
    store.append("IDEM-2", second, h2)

    assert store.verify_chain() is True
    assert len(store.snapshot()) == 2


def test_audit_store_rejects_tampered_event_hash():
    from src.core.persistence_controls import AppendOnlyAuditStore, PersistenceControlError
    import hashlib
    import json

    store = AppendOnlyAuditStore()
    payload = {"action": "G1"}
    raw = json.dumps(
        {"previousHash": "GENESIS", "payload": payload},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode()
    valid = hashlib.sha256(raw).hexdigest()

    with pytest.raises(PersistenceControlError):
        store.append("IDEM-TAMPER", payload, "0" * len(valid))
