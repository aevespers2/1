from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts import validate_evidence_retention_renewal as validator

FIXTURE = Path(os.environ.get("EVIDENCE_RETENTION_FIXTURE", "evidence/retention/producer-fixture.json"))


def _base_facts() -> dict[str, bool]:
    return {
        "source_identity_known": True,
        "artifact_digest_verified": True,
        "artifact_available": True,
        "retention_deadline_known": True,
        "retention_active": True,
        "tombstone_required": False,
        "tombstone_present": False,
        "renewal_attempted": False,
        "renewal_new_generation": False,
        "renewal_source_matches": True,
        "renewal_artifact_reverified": True,
        "renewal_independent_verifier": True,
        "claim_current": True,
        "claim_rebound_to_renewal": False,
        "claim_downgraded_or_withdrawn": False,
        "legal_hold_active": False,
        "legal_hold_promoted_to_currentness": False,
        "copy_or_migration": False,
        "copy_reverified": True,
        "deletion_requested": False,
        "deletion_propagated": True,
        "rollback_reintroduces_expired": False,
        "claim_validity_within_retention": True,
    }


def _case(case_id: str, **changes: bool) -> dict[str, object]:
    facts = _base_facts()
    facts.update(changes)
    disposition, reasons = validator.evaluate(facts)
    return {
        "case_id": case_id,
        "facts": facts,
        "expected": {"disposition": disposition, "reasons": reasons},
    }


def synthetic_payload() -> dict[str, object]:
    """Build a complete local corpus so hostile tests never depend on a download."""
    cases = [
        _case("source_unknown", source_identity_known=False),
        _case("digest_unverified", artifact_digest_verified=False),
        _case("deadline_unknown", retention_deadline_known=False),
        _case("expired_current", retention_active=False),
        _case("artifact_unavailable", artifact_available=False),
        _case("tombstone_missing", tombstone_required=True),
        _case("renewal_mutates", renewal_attempted=True),
        _case(
            "renewal_source_mismatch",
            renewal_attempted=True,
            renewal_new_generation=True,
            renewal_source_matches=False,
            claim_rebound_to_renewal=True,
        ),
        _case(
            "renewal_unverified",
            renewal_attempted=True,
            renewal_new_generation=True,
            renewal_artifact_reverified=False,
            claim_current=False,
        ),
        _case(
            "renewal_not_independent",
            renewal_attempted=True,
            renewal_new_generation=True,
            renewal_independent_verifier=False,
            claim_current=False,
        ),
        _case(
            "claim_not_rebound",
            renewal_attempted=True,
            renewal_new_generation=True,
        ),
        _case(
            "legal_hold_promoted",
            legal_hold_active=True,
            legal_hold_promoted_to_currentness=True,
        ),
        _case("copy_not_reverified", copy_or_migration=True, copy_reverified=False),
        _case("deletion_partial", deletion_requested=True, deletion_propagated=False),
        _case("rollback_expired", rollback_reintroduces_expired=True),
        _case("claim_window_mismatch", claim_validity_within_retention=False),
        _case("current"),
        _case(
            "renewal_pending_rebinding",
            renewal_attempted=True,
            renewal_new_generation=True,
            claim_current=False,
        ),
        _case(
            "historical",
            retention_active=False,
            claim_current=False,
            claim_downgraded_or_withdrawn=True,
        ),
        _case(
            "tombstoned",
            artifact_available=False,
            tombstone_required=True,
            tombstone_present=True,
            claim_current=False,
        ),
    ]
    return {
        "profile_id": validator.PROFILE_ID,
        "version": validator.PROFILE_VERSION,
        "fact_fields": list(validator.FACT_FIELDS),
        "reason_order": list(validator.REASON_ORDER),
        "dispositions": list(validator.DISPOSITIONS),
        "cases": cases,
    }


class EvidenceRetentionRenewalContractTests(unittest.TestCase):
    def payload(self):
        return synthetic_payload()

    def producer_payload(self):
        if not FIXTURE.is_file():
            self.skipTest(f"producer fixture is supplied by exact-head CI: {FIXTURE}")
        return validator.strict_load(FIXTURE)

    def write_payload(self, payload) -> Path:
        handle = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        with handle:
            handle.write(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        return Path(handle.name)

    def assert_rejected(self, payload) -> None:
        path = self.write_payload(payload)
        self.addCleanup(path.unlink, missing_ok=True)
        with self.assertRaises(ValueError):
            validator.validate_payload(validator.strict_load(path))

    def test_local_synthetic_corpus_covers_every_reason_and_disposition(self):
        cases = validator.validate_payload(self.payload())
        self.assertEqual(len(cases), validator.EXPECTED_CASE_COUNT)

    def test_producer_fixture_passes_independent_derivation(self):
        cases = validator.validate_payload(self.producer_payload())
        self.assertEqual(len(cases), validator.EXPECTED_CASE_COUNT)

    def test_duplicate_key_rejected_before_semantic_validation(self):
        path = Path(tempfile.mkstemp(suffix=".json")[1])
        self.addCleanup(path.unlink, missing_ok=True)
        path.write_text('{"version":1,"version":1}', encoding="utf-8")
        with self.assertRaises(ValueError):
            validator.strict_load(path)

    def test_invalid_utf8_rejected(self):
        path = Path(tempfile.mkstemp(suffix=".json")[1])
        self.addCleanup(path.unlink, missing_ok=True)
        path.write_bytes(b'{"profile_id":"x","bad":"\xff"}')
        with self.assertRaises(ValueError):
            validator.strict_load(path)

    def test_unknown_top_level_field_rejected(self):
        payload = self.payload()
        payload["authority"] = True
        self.assert_rejected(payload)

    def test_sensitive_field_rejected(self):
        payload = self.payload()
        payload["cases"][0]["facts"]["private_key_material"] = False
        self.assert_rejected(payload)

    def test_fact_registry_order_drift_rejected(self):
        payload = self.payload()
        payload["fact_fields"] = list(reversed(payload["fact_fields"]))
        self.assert_rejected(payload)

    def test_non_boolean_fact_rejected(self):
        payload = self.payload()
        payload["cases"][0]["facts"]["artifact_available"] = "true"
        self.assert_rejected(payload)

    def test_expected_disposition_drift_rejected(self):
        payload = self.payload()
        payload["cases"][0]["expected"]["disposition"] = "EVIDENCE_CURRENT"
        self.assert_rejected(payload)

    def test_reason_order_drift_rejected(self):
        payload = self.payload()
        target = next(case for case in payload["cases"] if len(case["expected"]["reasons"]) > 1)
        target["expected"]["reasons"].reverse()
        self.assert_rejected(payload)

    def test_missing_case_rejected(self):
        payload = self.payload()
        payload["cases"].pop()
        self.assert_rejected(payload)

    def test_unregistered_reason_rejected(self):
        payload = self.payload()
        payload["reason_order"].append("UNREGISTERED_REASON")
        self.assert_rejected(payload)


if __name__ == "__main__":
    unittest.main()
