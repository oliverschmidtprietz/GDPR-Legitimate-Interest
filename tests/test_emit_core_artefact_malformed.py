"""Regression tests mirroring toms-art32's adversarial-review discipline
(ADVERSARIAL-REVIEW-2026-09-08.md, finding 3): --emit-core-artefact must never
crash on malformed input, must leave the report/exit code unchanged, and must
still write a schema-valid (blocked, where appropriate) artefact.
"""
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

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


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


MUTATIONS = {
    "assessment-not-an-object": lambda s: s.__setitem__("assessment", 42),
    "gaps-entry-is-null": lambda s: s.__setitem__("gaps", [None]),
    "generated-at-is-null": lambda s: s.__setitem__("generated_at", None),
    "overall-verdict-is-invalid": lambda s: s["overall"].__setitem__("li_appropriate", "maybe"),
}


@pytest.mark.parametrize("name", MUTATIONS)
def test_malformed_sidecar_leaves_report_and_exit_code_unchanged(tmp_path, name):
    sidecar = _load_fixture()
    MUTATIONS[name](sidecar)
    mutated_path = tmp_path / f"{name}.json"
    mutated_path.write_text(json.dumps(sidecar), encoding="utf-8")

    baseline = run_cli(mutated_path, "--format", "json")
    out = tmp_path / "core.json"
    with_flag = run_cli(mutated_path, "--emit-core-artefact", out, "--format", "json")

    assert with_flag.returncode == baseline.returncode
    baseline_report = json.loads(baseline.stdout)
    with_flag_report = json.loads(with_flag.stdout)
    # validated_at is a fresh wall-clock timestamp stamped independently by each subprocess
    # run — normalise it before comparing; every other field is compared exactly.
    baseline_report["validated_at"] = "<normalised>"
    with_flag_report["validated_at"] = "<normalised>"
    assert with_flag_report == baseline_report
    assert with_flag.stderr == "" or "Traceback" not in with_flag.stderr


@pytest.mark.parametrize("name", MUTATIONS)
def test_malformed_sidecar_still_writes_a_schema_valid_artefact(tmp_path, name):
    sidecar = _load_fixture()
    MUTATIONS[name](sidecar)
    mutated_path = tmp_path / f"{name}.json"
    mutated_path.write_text(json.dumps(sidecar), encoding="utf-8")

    out = tmp_path / "core.json"
    proc = run_cli(mutated_path, "--emit-core-artefact", out, "--format", "json")

    assert out.exists(), f"no artefact written for {name}; stderr={proc.stderr}"
    artefact = json.loads(out.read_text(encoding="utf-8"))
    jsonschema.validate(artefact, ARTEFACT_SCHEMA,
                        format_checker=jsonschema.FormatChecker())

    envelope = json.loads(proc.stdout)
    assert envelope["status"] == "failed"
    assert artefact["outcome"]["status"] == "blocked"


def test_generated_at_null_never_copies_null_into_the_artefact(tmp_path):
    sidecar = _load_fixture()
    sidecar["generated_at"] = None
    mutated_path = tmp_path / "generated-at-null.json"
    mutated_path.write_text(json.dumps(sidecar), encoding="utf-8")

    out = tmp_path / "core.json"
    run_cli(mutated_path, "--emit-core-artefact", out)

    artefact = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(artefact["generated_at"], str) and artefact["generated_at"]
