from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    role: str
    allowed_gates: tuple[str, ...]
    can_release_externally: bool = False

AGENTS = {
    "intake": AgentSpec("intake", "Intake Assistant", ("G0", "G1", "G2")),
    "legal": AgentSpec("legal", "Legal/Rules Assistant", ("G3", "G4", "G5")),
    "execution": AgentSpec("execution", "Execution Assistant", ("G6", "G7", "G8", "G9")),
    "release": AgentSpec("release", "Human Release Coordinator", ("G10",)),
    "connector": AgentSpec("connector", "External Connector Assistant", ("G11", "G12")),
    "evidence": AgentSpec("evidence", "Primary Evidence Assistant", ("G13", "G14")),
    "reconciliation": AgentSpec("reconciliation", "Reconciliation Assistant", ("G15", "G16")),
    "closure": AgentSpec("closure", "Enforcement/Closure Assistant", ("G17", "G18", "G19")),
}

class AgentControlError(Exception):
    pass

def authorize_agent(agent_id: str, gate: str, *, human_release: bool = False) -> AgentSpec:
    spec = AGENTS.get(agent_id)
    if spec is None or gate not in spec.allowed_gates:
        raise AgentControlError("Agent is not authorized for this gate.")
    if gate == "G10" and not human_release:
        raise AgentControlError("G10 requires explicit human release.")
    return spec

def execute_controlled(agent_id: str, gate: str, action: Callable[[], Any], *, human_release: bool = False) -> Any:
    authorize_agent(agent_id, gate, human_release=human_release)
    return action()
