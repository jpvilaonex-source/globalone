import pytest

from src.connectors.omni_gateway_connector import OmniGatewayConnector
from src.gateways.omni_gateway_engine import EvidenceIngressError, OmniGatewayEngine


def test_unknown_gateway_is_rejected():
    engine = OmniGatewayEngine()
    with pytest.raises(EvidenceIngressError):
        engine.ingest_primary_evidence("UNKNOWN", {}, source_verified=True, authenticity_verified=True)


def test_unverified_evidence_cannot_enter_g13():
    engine = OmniGatewayEngine()
    with pytest.raises(EvidenceIngressError):
        engine.ingest_primary_evidence(
            "GW-WA-COURT-01", {"status": "anything"},
            source_verified=False, authenticity_verified=True,
        )


def test_unauthenticated_evidence_cannot_enter_g14():
    engine = OmniGatewayEngine()
    with pytest.raises(EvidenceIngressError):
        engine.ingest_primary_evidence(
            "GW-LAND-TITLE-02", {"title": "anything"},
            source_verified=True, authenticity_verified=False,
        )


def test_connector_fails_closed_without_live_provider():
    connector = OmniGatewayConnector("GW-WA-COURT-01", "WA Courts")
    assert connector.authenticate_session() is False
    with pytest.raises(ConnectionError):
        connector.submit_payload({"masterReference": "1251254"}, True)
    with pytest.raises(ConnectionError):
        connector.fetch_primary_evidence("receipt")


def test_reconciliation_detects_mismatch():
    engine = OmniGatewayEngine()
    engine.ingest_primary_evidence(
        "GW-ASIC-CORP-03", {"status": "ACTIVE"},
        source_verified=True, authenticity_verified=True,
    )
    result = engine.reconcile({"GW-ASIC-CORP-03": {"status": "INACTIVE"}})
    assert result["matched"] is False
    assert "status" in result["discrepancies"]["GW-ASIC-CORP-03"]


def test_reconciliation_matches_exact_evidence():
    engine = OmniGatewayEngine()
    engine.ingest_primary_evidence(
        "GW-WA-COURT-01", {"status": "ORDER_ENTERED"},
        source_verified=True, authenticity_verified=True,
    )
    result = engine.reconcile({"GW-WA-COURT-01": {"status": "ORDER_ENTERED"}})
    assert result["matched"] is True
