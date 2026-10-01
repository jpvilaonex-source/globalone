from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import BaseConnector


@dataclass(frozen=True)
class GatewayDescriptor:
    gateway_id: str
    provider: str
    jurisdiction: str
    capability: str


GATEWAYS = {
    "GW-WA-COURT-01": GatewayDescriptor("GW-WA-COURT-01", "WA Courts", "AU-WA", "PRIMARY_EVIDENCE"),
    "GW-LAND-TITLE-02": GatewayDescriptor("GW-LAND-TITLE-02", "Landgate", "AU-WA", "PRIMARY_EVIDENCE"),
    "GW-ASIC-CORP-03": GatewayDescriptor("GW-ASIC-CORP-03", "ASIC", "AU-CTH", "PRIMARY_EVIDENCE"),
    "GW-REVENUE-04": GatewayDescriptor("GW-REVENUE-04", "WA Department of Finance", "AU-WA", "PRIMARY_EVIDENCE"),
    "GW-FEDERAL-05": GatewayDescriptor("GW-FEDERAL-05", "Federal Court / High Court registry", "AU-CTH", "PRIMARY_EVIDENCE"),
    "GW-BANK-06": GatewayDescriptor("GW-BANK-06", "Banking / settlement provider", "AU", "FINANCIAL_EVIDENCE"),
}


class OmniGatewayConnector(BaseConnector):
    """Fail-closed gateway contract.

    This module does not manufacture receipts, seals, registry records, or
    external status. A concrete provider adapter must implement live I/O.
    """

    def __init__(self, connector_id: str, provider: str, *, transport: Any = None):
        super().__init__(connector_id, provider)
        self.transport = transport

    def authenticate_session(self) -> bool:
        if self.transport is None:
            return False
        return bool(self.transport.authenticate())

    def submit_payload(self, payload: Dict[str, Any], release_gate_cleared: bool) -> Dict[str, Any]:
        if not release_gate_cleared:
            raise PermissionError("G11 transmission blocked until G10 human release.")
        if self.transport is None:
            raise ConnectionError("No live provider adapter configured; transmission not executed.")
        return self.transport.submit(payload)

    def fetch_primary_evidence(self, receipt_id: str) -> Dict[str, Any]:
        if self.transport is None:
            raise ConnectionError("No live provider adapter configured; primary evidence not retrieved.")
        return self.transport.fetch_primary_evidence(receipt_id)


def build_gateway_registry() -> dict[str, GatewayDescriptor]:
    return dict(GATEWAYS)
