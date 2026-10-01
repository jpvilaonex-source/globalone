from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List

VALID_GATES: List[str] = [f"G{i}" for i in range(20)]


class GateTransitionException(Exception):
    pass


class GateStateEngine:
    """Deterministic, fail-closed G0-G19 state machine for Master Reference 1251254."""

    def __init__(self, component_id: str, current_gate_index: int = 0):
        if not component_id or not component_id.strip():
            raise ValueError("Component ID is required.")
        if not 0 <= current_gate_index < len(VALID_GATES):
            raise ValueError("Invalid initial gate")
        self._master_reference = "1251254"
        self._component_id = component_id
        self._current_gate_index = current_gate_index
        self._state_history: List[Dict[str, Any]] = []
        self._transition_lock = Lock()

    @property
    def master_reference(self) -> str:
        return self._master_reference

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def current_gate_index(self) -> int:
        return self._current_gate_index

    @property
    def state_history(self) -> tuple[Dict[str, Any], ...]:
        return tuple(dict(event) for event in self._state_history)

    def get_current_gate(self) -> str:
        return VALID_GATES[self._current_gate_index]

    def transition_to(
        self, target_gate: str, actor: str, *, evidence_provided=False,
        human_authorisation=False, receipt_provided=False,
        authenticity_checked=False, reconciled=False
    ) -> str:
        if not actor or not actor.strip():
            raise GateTransitionException("Actor is required.")
        with self._transition_lock:
            if target_gate not in VALID_GATES:
                raise GateTransitionException(f"Invalid target gate: {target_gate}")
            target = VALID_GATES.index(target_gate)
            if target != self._current_gate_index + 1:
                raise GateTransitionException(
                    "Gate transition must be strictly sequential; no retroactive gate bypass."
                )
            if target == 10 and not human_authorisation:
                raise GateTransitionException(
                    "G10 requires explicit human release authorization."
                )
            if target == 12 and not receipt_provided:
                raise GateTransitionException("G12 requires an external receipt.")
            if target == 13 and not evidence_provided:
                raise GateTransitionException(
                    "G13 requires primary authoritative evidence."
                )
            if target == 14 and not authenticity_checked:
                raise GateTransitionException(
                    "G14 requires source authenticity verification."
                )
            if target == 15 and not reconciled:
                raise GateTransitionException("G15 requires reconciliation.")
            if target == 16 and not (
                evidence_provided and authenticity_checked and reconciled
            ):
                raise GateTransitionException(
                    "G16 requires evidence-backed G13-G15 clearance."
                )

            previous = self.get_current_gate()
            new = VALID_GATES[target]
            event = {
                "masterReference": self._master_reference,
                "componentId": self._component_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": actor,
                "previousState": previous,
                "newState": new,
            }
            self._current_gate_index = target
            self._state_history.append(event)
            return new
