import unittest
from src.core.gate_engine import GateStateEngine, GateTransitionException

class TestGateStateEngine(unittest.TestCase):
    def test_initial(self):
        self.assertEqual(GateStateEngine("X").get_current_gate(),"G0")
    def test_no_jump(self):
        with self.assertRaises(GateTransitionException):
            GateStateEngine("X").transition_to("G5","test")
    def test_g10_barrier(self):
        e=GateStateEngine("X")
        for i in range(1,10): e.transition_to(f"G{i}","test")
        with self.assertRaises(GateTransitionException): e.transition_to("G10","test")
        e.transition_to("G10","human",human_authorisation=True)
        self.assertEqual(e.get_current_gate(),"G10")
    def test_g13_g16_chain(self):
        e=GateStateEngine("X")
        for i in range(1,13):
            e.transition_to(f"G{i}","test",human_authorisation=(i==10))
        with self.assertRaises(GateTransitionException): e.transition_to("G13","source")
        e.transition_to("G13","source",evidence_provided=True)
        e.transition_to("G14","source",evidence_provided=True,authenticity_checked=True)
        e.transition_to("G15","reconciler",evidence_provided=True,authenticity_checked=True,reconciled=True)
        e.transition_to("G16","verifier",evidence_provided=True,authenticity_checked=True,reconciled=True)

if __name__=="__main__": unittest.main()
