"""Rule coverage: RUNNER-0 (empty-registry guard), SCHEMA-1, LOGIC-1, ORDER-1,
COMPLETE-1, SRC-1 — each proven to fire as a Finding (never an exception), and
proven to fire ALONE on its own must_fail fixture (never collaterally trip an
unrelated rule).
"""
import json
from pathlib import Path

import pytest

from lia_validator.runner import validate, Context, Result
from lia_validator.registry import RULES
import lia_validator.rules  # noqa: F401  (populates the registry)

HERE = Path(__file__).resolve()
SKILL_ROOT = HERE.parents[1]
VALIDATOR = SKILL_ROOT / "validator"
SCHEMA = VALIDATOR.parent / "references" / "legitimate-interest-sidecar-schema.json"
REFERENCES_DIR = VALIDATOR.parent / "references"
FIX = VALIDATOR / "fixtures"

ALL_RULE_IDS = {"SCHEMA-1", "LOGIC-1", "ORDER-1", "COMPLETE-1", "SRC-1"}


def _ctx(sources_lock_override=None, references_dir=REFERENCES_DIR):
    return Context(mode="internal", schema_path=SCHEMA, references_dir=references_dir,
                   sources_lock_override=sources_lock_override)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rejecting_rule_ids(result: Result) -> set:
    return {f.rule_id for f in result.findings if f.severity == "rejection"}


def test_rules_registry_is_populated_by_importing_the_package():
    assert ALL_RULE_IDS <= set(RULES.keys())


def test_runner_0_fails_closed_when_registry_is_empty(monkeypatch):
    import lia_validator.registry as registry_module
    monkeypatch.setattr(registry_module, "RULES", {})
    # runner.py imports the RULES dict by reference at import time (`from .registry import
    # RULES`), so patch the SAME dict object runner.py holds, not the module attribute.
    import lia_validator.runner as runner_module
    monkeypatch.setattr(runner_module, "RULES", {})
    result = validate(_load(FIX / "must_pass" / "minimal-clean.json"), _ctx())
    assert result.status == "failed"
    assert result.summary["rejections"] == 1
    assert result.findings[0].rule_id == "RUNNER-0"


def test_minimal_clean_passes_with_zero_findings():
    result = validate(_load(FIX / "must_pass" / "minimal-clean.json"), _ctx())
    assert result.findings == [], [f.to_dict() for f in result.findings]
    assert result.status == "passed"


def test_step1_fail_shortcircuit_clean_passes_with_zero_findings():
    result = validate(_load(FIX / "must_pass" / "step1-fail-shortcircuit-clean.json"), _ctx())
    assert result.findings == [], [f.to_dict() for f in result.findings]
    assert result.status == "passed"


@pytest.mark.parametrize("fixture_name,rule_id", [
    ("SCHEMA-1__bad-verdict-enum.json", "SCHEMA-1"),
    ("LOGIC-1__step1-fail-overall-yes.json", "LOGIC-1"),
])
def test_must_fail_fixture_trips_exactly_its_named_rejecting_rule(fixture_name, rule_id):
    sidecar = _load(FIX / "must_fail" / fixture_name)
    result = validate(sidecar, _ctx())
    assert result.status == "failed"
    assert _rejecting_rule_ids(result) == {rule_id}, [f.to_dict() for f in result.findings]


@pytest.mark.parametrize("fixture_name,rule_id", [
    ("ORDER-1__step1-fail-step2-verdict-present.json", "ORDER-1"),
    ("COMPLETE-1__missing-step3-verdict.json", "COMPLETE-1"),
])
def test_must_fail_fixture_trips_exactly_its_named_warning_rule(fixture_name, rule_id):
    # ORDER-1 and COMPLETE-1 are severity="warning", not "rejection", so they are checked
    # separately from the rejection-only fixtures above: a warning-only run is
    # "passed_with_warnings", not "failed".
    sidecar = _load(FIX / "must_fail" / fixture_name)
    result = validate(sidecar, _ctx())
    assert result.status == "passed_with_warnings"
    assert _rejecting_rule_ids(result) == set()
    warning_rule_ids = {f.rule_id for f in result.findings if f.severity == "warning"}
    assert warning_rule_ids == {rule_id}, [f.to_dict() for f in result.findings]


def test_src_1_missing_manifest_entry_is_flagged():
    override = {
        "schema_version": "1.0",
        "generated_at": "2026-09-24",
        "files": {
            "references/step1-legitimate-interest.md": {
                "source_type": "ai-drafted", "jurisdiction": "EU", "url": None,
                "last_verified": "2026-06-11", "confidence": "high",
                "owner": "oliverschmidtprietz",
            },
        },
    }
    result = validate(_load(FIX / "must_pass" / "minimal-clean.json"),
                       _ctx(sources_lock_override=override))
    findings = [f for f in result.findings if f.rule_id == "SRC-1"]
    assert findings, "SRC-1 must fire when an on-disk references/*.md file has no manifest entry"
    assert any("step2-necessity.md" in f.message for f in findings), [f.to_dict() for f in findings]
    for f in findings:
        assert f.severity == "warning"
        assert f.priority == "high"


def test_src_1_stale_manifest_entry_is_flagged():
    override = {
        "schema_version": "1.0",
        "generated_at": "2026-09-24",
        "files": {
            "references/step1-legitimate-interest.md": {
                "source_type": "ai-drafted", "jurisdiction": "EU", "url": None,
                "last_verified": "2024-01-01", "confidence": "high",
                "owner": "oliverschmidtprietz",
            },
        },
    }
    result = validate(_load(FIX / "must_pass" / "minimal-clean.json"),
                       _ctx(sources_lock_override=override))
    findings = [f for f in result.findings if f.rule_id == "SRC-1"]
    stale = [f for f in findings if "step1-legitimate-interest.md" in f.message and "2024-01-01" in f.message]
    assert stale, [f.to_dict() for f in findings]


def test_src_1_malformed_manifest_is_flagged_without_raising():
    result = validate(_load(FIX / "must_pass" / "minimal-clean.json"),
                       _ctx(sources_lock_override=[]))   # MUST NOT raise
    findings = [f for f in result.findings if f.rule_id == "SRC-1"]
    assert findings, "a malformed (non-object) manifest must be flagged, not silently skipped"
    assert not any(f.severity == "rejection" for f in result.findings)
    assert result.status != "failed"


def test_src_1_real_manifest_produces_zero_findings():
    real_manifest = SKILL_ROOT / "sources.lock.json"
    assert real_manifest.exists(), "skills/legitimate-interest/sources.lock.json must exist"
    result = validate(_load(FIX / "must_pass" / "minimal-clean.json"),
                       _ctx(sources_lock_override=None))
    findings = [f for f in result.findings if f.rule_id == "SRC-1"]
    assert findings == [], [f.to_dict() for f in findings]
