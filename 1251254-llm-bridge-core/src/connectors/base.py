from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseConnector(ABC):
    def __init__(self, connector_id: str, provider: str):
        self.master_reference="1251254"; self.connector_id=connector_id; self.provider=provider

    @abstractmethod
    def authenticate_session(self) -> bool: ...

    @abstractmethod
    def submit_payload(self, payload: Dict[str, Any], release_gate_cleared: bool) -> Dict[str, Any]:
        if not release_gate_cleared:
            raise PermissionError("G11 transmission blocked until G10 human release.")
        ...

    @abstractmethod
    def fetch_primary_evidence(self, receipt_id: str) -> Dict[str, Any]: ...
