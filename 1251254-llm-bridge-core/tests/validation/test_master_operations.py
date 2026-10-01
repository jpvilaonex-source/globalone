import pytest

from src.core.agent_control import AgentControlError, authorize_agent
from src.core.persistence_controls import AppendOnlyAuditStore, PersistenceControlError
from src.core.operations import OperationsController


def test_agent_boundaries_and_g10_release():
    assert authorize_agent("intake", "G0").agent_id == "intake"
    with pytest.raises(AgentControlError):
        authorize_agent("intake", "G10")
    with pytest.raises(AgentControlError):
        authorize_agent("release", "G10", human_release=False)
    assert authorize_agent("release", "G10", human_release=True).agent_id == "release"


def test_append_only_store_blocks_replay_and_preserves_chain():
    store = AppendOnlyAuditStore()
    first = store.append("op-1", {"gate": "G1"}, "hash-1")
    second = store.append("op-2", {"gate": "G2"}, "hash-2")
    assert second.previous_hash == first.event_hash
    with pytest.raises(PersistenceControlError):
        store.append("op-1", {"gate": "G99"}, "hash-evil")
    assert len(store.snapshot()) == 2


def test_operations_are_explicit_and_evidence_gated():
    ops = OperationsController()
    assert ops.backup().status == "READY_FOR_CONTROLLED_BACKEND"
    assert ops.sync().status == "READY_FOR_CONTROLLED_RECONCILIATION"
    assert ops.verify().status == "READY_FOR_EXECUTION"
    assert ops.recover().status == "READY_FOR_CONTROLLED_RESTORE"
