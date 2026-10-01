from dataclasses import dataclass

@dataclass(frozen=True)
class ReconciliationResult:
    matched: bool
    discrepancies: tuple[str, ...]

def reconcile(expected: dict, observed: dict) -> ReconciliationResult:
    discrepancies=tuple(sorted(k for k in set(expected)|set(observed) if expected.get(k)!=observed.get(k)))
    return ReconciliationResult(not discrepancies, discrepancies)
