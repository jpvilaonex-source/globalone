from src.evidence.gemini_evidence import GeminiEvidenceRecord, GeminiEvidenceRegister

def test_gemini_record_has_dual_digest_and_separate_fields():
    r = GeminiEvidenceRecord(
        "EX-GEM-001", "original-export.json", "conv-1", "Original statement",
        "2026-10-01T00:00:00Z", "Proposition", "Gemini",
        "Materiality basis", ("contradiction-1",), ("source-1",)
    )
    assert len(r.sha256()) == 64
    assert len(r.sha512()) == 128
    assert r.sha256() == r.sha256()

def test_register_is_master_bound_and_snapshot_is_read_only():
    reg = GeminiEvidenceRegister()
    r = GeminiEvidenceRecord(
        "EX-GEM-002", "source.json", "conv-2", "Statement", "2026-10-01T00:00:00Z",
        "Prop", "Gemini", "Basis", (), ()
    )
    reg.add(r)
    snap = reg.snapshot()
    assert len(snap) == 1
    assert reg.manifest()["legalStatus"] == "EVIDENCE_REGISTER_ONLY_NO_OFFENCE_DETERMINATION"
