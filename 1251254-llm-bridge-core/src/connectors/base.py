from abc import ABC, abstractmethod
from typing import Any, Dict


class ConnectorSecurityException(PermissionError):
    """Raised when a connector attempts an unsafe external operation."""


class BaseConnector(ABC):
    def __init__(self, connector_id: str, provider: str):
        if not connector_id or not connector_id.strip():
            raise ValueError("Connector ID is required.")
        if not provider or not provider.strip():
            raise ValueError("Provider is required.")
        self._master_reference = "1251254"
        self._connector_id = connector_id
        self._provider = provider

    @property
    def master_reference(self) -> str:
        return self._master_reference

    @property
    def connector_id(self) -> str:
        return self._connector_id

    @property
    def provider(self) -> str:
        return self._provider

    @abstractmethod
    def authenticate_session(self) -> bool:
        ...

    def submit_payload(
        self,
        payload: Dict[str, Any],
        release_gate_cleared: bool,
        *,
        external_submission_authorised: bool = False,
    ) -> Dict[str, Any]:
        """Fail-closed external transmission boundary.

        A connector may transmit only after G10 human release and an explicit
        external-submission authorization assertion. This method does not claim
        that a provider accepted the payload; provider receipt must be captured
        separately at G12.
        """
        if not release_gate_cleared:
            raise ConnectorSecurityException(
                "G11 transmission blocked until G10 human release."
            )
        if not external_submission_authorised:
            raise ConnectorSecurityException(
                "G11 transmission blocked until explicit external-submission authorization."
            )
        if not isinstance(payload, dict):
            raise TypeError("Connector payload must be a dictionary.")
        if not self.authenticate_session():
            raise ConnectionError(f"Authentication failed for {self._provider}.")
        return self._transmit(payload)

    @abstractmethod
    def _transmit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

    @abstractmethod
    def fetch_primary_evidence(self, receipt_id: str) -> Dict[str, Any]:
        ...
