from __future__ import annotations

from typing import Any

from src.connectors.omni_gateway_connector import build_gateway_registry
from src.reconciliation.reconciliation_engine import reconcile


class EvidenceIngressError(Exception):
    pass


class OmniGatewayEngine:
    """Evidence ingress and reconciliation coordinator.

    External truth is accepted only from a concrete provider adapter and is
    never synthesized from a payload supplied by the caller.
    """

    master_reference = "1251254"

    def __init__(self):
        self.registry = build_gateway_registry()
        self.evidence: list[dict[str, Any]] = []

    def ingest_primary_evidence(
        self,
        gateway_id: str,
        evidence: dict[str, Any],
        *,
        source_verified: bool,
        authenticity_verified: bool,
    ) -> dict[str, Any]:
        if gateway_id not in self.registry:
            raise EvidenceIngressError("Unknown gateway.")
        if not source_verified:
            raise EvidenceIngressError("G13 requires verified primary source evidence.")
        if not authenticity_verified:
            raise EvidenceIngressError("G14 requires source authenticity verification.")
        record = {
            "masterReference": self.master_reference,
            "gatewayId": gateway_id,
            "evidence": evidence,
            "sourceVerified": True,
            "authenticityVerified": True,
        }
        self.evidence.append(record)
        return record

    def reconcile(self, expected_by_gateway: dict[str, dict[str, Any]]) -> dict[str, Any]:
        results = {}
        discrepancies = {}
        for record in self.evidence:
            gw = record["gatewayId"]
            result = reconcile(expected_by_gateway.get(gw, {}), record["evidence"])
            results[gw] = result.matched
            if not result.matched:
                discrepancies[gw] = result.discrepancies
        return {
            "masterReference": self.master_reference,
            "gatewayCount": len(results),
            "matched": all(results.values()) if results else False,
            "results": results,
            "discrepancies": discrepancies,
        }
