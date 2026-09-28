"""CLI tests for --emit-core-artefact (portfolio standard, structural tier).

Same contract as toms-art32's/ropa's flag: the emitted artefact is built from
the LIVE validation result, never the sidecar's embedded validation block, and
sources[]/handoffs[]/unknowns[] must be driven by real input, never hard-coded
empty (SIX-SKILL-ADOPTION-BRIEF-2026-09-24.md's anti-empty rule).
"""
import json
import subprocess
import sys
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATE = REPO_ROOT / "skills" / "legitimate-interest" / "validator" / "validate.py"
FIXTURE = (REPO_ROOT / "skills" / "legitimate-interest" / "validator" / "fixtures"
           / "must_pass" / "minimal-clean.json")
ARTEFACT_SCHEMA = json.loads(
    (REPO_ROOT / "docs" / "standards" / "schemas"
     / "skill-artefact-1.1.schema.json").read_text(encoding="utf-8"))


def run_cli(*argv):
    return subprocess.run(
        [sys.executable, str(VALIDATE), *map(str, argv)],
        capture_output=True, text=True)


def test_emit_writes_schema_valid_core_artefact_and_leaves_report_unchanged(tmp_path):
    out = tmp_path / "core.json"
    proc = run_cli(FIXTURE, "--emit-core-artefact", out, "--format", "json")
    assert proc.returncode == 0, proc.stderr
    artefact = json.loads(out.read_text(encoding="utf-8"))
    jsonschema.validate(artefact, ARTEFACT_SCHEMA,
                        format_checker=jsonschema.FormatChecker())
    assert artefact["skill"] == "legitimate-interest"
    assert artefact["subject"]["type"] == "processing_activity"
    envelope = json.loads(proc.stdout)
    assert envelope["report_schema_version"] == "2.0"


def test_emit_reflects_live_result_not_embedded_validation_block(tmp_path):
    sidecar = json.loads(FIXTURE.read_text(encoding="utf-8"))
    sidecar["validation"] = {"status": "failed", "findings": []}
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(sidecar), encoding="utf-8")
    out = tmp_path / "core.json"
    proc = run_cli(tampered, "--emit-core-artefact", out)
    assert proc.returncode == 0, proc.stderr
    artefact = json.loads(out.read_text(encoding="utf-8"))
    assert artefact["outcome"]["status"] == "complete"


def test_emit_populates_sources_from_sources_lock_not_hard_coded_empty(tmp_path):
    out = tmp_path / "core.json"
    run_cli(FIXTURE, "--emit-core-artefact", out)
    artefact = json.loads(out.read_text(encoding="utf-8"))
    assert artefact["sources"], "sources[] must be populated from sources.lock.json, not []"
    ids = {s["id"] for s in artefact["sources"]}
    assert "references/step1-legitimate-interest.md" in ids


def test_emit_populates_handoffs_when_overall_verdict_supports_article_21(tmp_path):
    # The fixture's overall.li_appropriate is "yes", so the data-subject-rights handoff
    # (SKILL.md "Right to Object Response Mode") must be populated, not hard-coded empty.
    out = tmp_path / "core.json"
    run_cli(FIXTURE, "--emit-core-artefact", out)
    artefact = json.loads(out.read_text(encoding="utf-8"))
    assert artefact["handoffs"], "handoffs[] must be populated when li_appropriate is yes/conditional"
    assert artefact["handoffs"][0]["sibling_skill"] == "data-subject-rights"


def test_emit_omits_handoffs_when_li_appropriate_is_no(tmp_path):
    sidecar = json.loads(FIXTURE.read_text(encoding="utf-8"))
    sidecar["overall"]["li_appropriate"] = "no"
    mutated = tmp_path / "no-verdict.json"
    mutated.write_text(json.dumps(sidecar), encoding="utf-8")
    out = tmp_path / "core.json"
    run_cli(mutated, "--emit-core-artefact", out)
    artefact = json.loads(out.read_text(encoding="utf-8"))
    assert artefact["handoffs"] == []


def test_emit_populates_unknowns_from_the_sidecars_own_gaps_register(tmp_path):
    out = tmp_path / "core.json"
    run_cli(FIXTURE, "--emit-core-artefact", out)
    artefact = json.loads(out.read_text(encoding="utf-8"))
    assert artefact["unknowns"], "unknowns[] must be populated from the sidecar's gaps[]"
    assert artefact["unknowns"][0]["id"] == "gap-001"
    assert artefact["unknowns"][0]["blocking"] is False
