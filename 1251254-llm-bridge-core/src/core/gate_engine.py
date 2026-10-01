from datetime import datetime, timezone
from typing import Dict, List

VALID_GATES: List[str] = [f"G{i}" for i in range(20)]

class GateTransitionException(Exception):
    pass

class GateStateEngine:
    def __init__(self, component_id: str, current_gate_index: int = 0):
        if not 0 <= current_gate_index < len(VALID_GATES):
            raise ValueError("Invalid initial gate")
        self.master_reference = "1251254"
        self.component_id = component_id
        self.current_gate_index = current_gate_index
        self.state_history: List[Dict] = []

    def get_current_gate(self) -> str:
        return VALID_GATES[self.current_gate_index]

    def transition_to(self, target_gate: str, actor: str, evidence_provided: bool = False,
                      human_authorisation: bool = False, receipt_provided: bool = False,
                      authenticity_checked: bool = False, reconciled: bool = False) -> str:
        if target_gate not in VALID_GATES:
            raise GateTransitionException(f"Invalid target gate: {target_gate}")
        target = VALID_GATES.index(target_gate)
        if target != self.current_gate_index + 1:
            raise GateTransitionException("Gate transition must be strictly sequential; no retroactive bypass.")
        if target == 10 and not human_authorisation:
            raise GateTransitionException("G10 requires explicit human release authorization.")
        if target == 12 and not receipt_provided:
            raise GateTransitionException("G12 requires an external receipt.")
        if target == 13 and not evidence_provided:
            raise GateTransitionException("G13 requires primary authoritative evidence.")
        if target == 14 and not authenticity_checked:
            raise GateTransitionException("G14 requires source authenticity verification.")
        if target == 15 and not reconciled:
            raise GateTransitionException("G15 requires reconciliation.")
        if target == 16 and not (evidence_provided and authenticity_checked and reconciled):
            raise GateTransitionException("G16 requires G13, G14 and G15 evidence-backed clearance.")
        previous = self.get_current_gate()
        self.current_gate_index = target
        new = self.get_current_gate()
        self.state_history.append({"masterReference":self.master_reference,"componentId":self.component_id,
            "timestamp":datetime.now(timezone.utc).isoformat(),"actor":actor,
            "previousState":previous,"newState":new})
        return new
