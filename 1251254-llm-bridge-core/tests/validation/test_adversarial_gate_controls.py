import unittest
from src.core.gate_engine import GateStateEngine, GateTransitionException


def advance_to_g12():
    e = GateStateEngine("ADVERSARIAL")
    for i in range(1, 13):
        e.transition_to(
            f"G{i}",
            "validator",
            human_authorisation=(i == 10),
            receipt_provided=(i == 12),
        )
    return e


class TestAdversarialGateControls(unittest.TestCase):
    def test_every_non_next_gate_is_rejected(self):
        e = GateStateEngine("X")
        for target in [f"G{i}" for i in range(2, 20)]:
            with self.assertRaises(GateTransitionException):
                e.transition_to(target, "attacker")
            self.assertEqual(e.get_current_gate(), "G0")

    def test_g10_rejects_missing_and_false_authorisation(self):
        e = GateStateEngine("X")
        for i in range(1, 10):
            e.transition_to(f"G{i}", "validator")
        for value in (False, None):
            with self.assertRaises(GateTransitionException):
                e.transition_to("G10", "automation", human_authorisation=value)
        self.assertEqual(e.get_current_gate(), "G9")

    def test_g12_rejects_missing_receipt(self):
        e = GateStateEngine("X")
        for i in range(1, 12):
            e.transition_to(f"G{i}", "validator", human_authorisation=(i == 10))
        with self.assertRaises(GateTransitionException):
            e.transition_to("G12", "connector", receipt_provided=False)
        self.assertEqual(e.get_current_gate(), "G11")

    def test_g13_requires_primary_evidence(self):
        e = advance_to_g12()
        with self.assertRaises(GateTransitionException):
            e.transition_to("G13", "source", evidence_provided=False)
        self.assertEqual(e.get_current_gate(), "G12")

    def test_g14_requires_authenticity(self):
        e = advance_to_g12()
        e.transition_to("G13", "source", evidence_provided=True)
        with self.assertRaises(GateTransitionException):
            e.transition_to("G14", "validator", authenticity_checked=False)
        self.assertEqual(e.get_current_gate(), "G13")

    def test_g15_requires_reconciliation(self):
        e = advance_to_g12()
        e.transition_to("G13", "source", evidence_provided=True)
        e.transition_to("G14", "validator", authenticity_checked=True)
        with self.assertRaises(GateTransitionException):
            e.transition_to("G15", "reconciler", reconciled=False)
        self.assertEqual(e.get_current_gate(), "G14")

    def test_g16_requires_all_three_evidence_conditions(self):
        e = advance_to_g12()
        e.transition_to("G13", "source", evidence_provided=True)
        e.transition_to("G14", "validator", authenticity_checked=True)
        e.transition_to("G15", "reconciler", reconciled=True)
        cases = [
            (False, True, True),
            (True, False, True),
            (True, True, False),
        ]
        for evidence, auth, recon in cases:
            with self.assertRaises(GateTransitionException):
                e.transition_to(
                    "G16", "verifier",
                    evidence_provided=evidence,
                    authenticity_checked=auth,
                    reconciled=recon,
                )
            self.assertEqual(e.get_current_gate(), "G15")

    def test_invalid_target_is_rejected_without_state_change(self):
        e = GateStateEngine("X")
        with self.assertRaises(GateTransitionException):
            e.transition_to("G20", "attacker")
        with self.assertRaises(GateTransitionException):
            e.transition_to("NOT_A_GATE", "attacker")
        self.assertEqual(e.get_current_gate(), "G0")

    def test_failed_transition_does_not_append_history(self):
        e = GateStateEngine("X")
        with self.assertRaises(GateTransitionException):
            e.transition_to("G5", "attacker")
        self.assertEqual(e.state_history, [])

    def test_complete_authorised_path_reaches_g19(self):
        e = advance_to_g12()
        e.transition_to("G13", "source", evidence_provided=True)
        e.transition_to("G14", "validator", authenticity_checked=True)
        e.transition_to("G15", "reconciler", reconciled=True)
        e.transition_to(
            "G16", "verifier",
            evidence_provided=True,
            authenticity_checked=True,
            reconciled=True,
        )
        for i in range(17, 20):
            e.transition_to(f"G{i}", "validator")
        self.assertEqual(e.get_current_gate(), "G19")
        self.assertEqual(len(e.state_history), 19)


if __name__ == "__main__":
    unittest.main()
