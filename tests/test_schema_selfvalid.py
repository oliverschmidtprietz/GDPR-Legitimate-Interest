import json
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA = Path(__file__).parents[1] / "references" / "legitimate-interest-sidecar-schema.json"


def _load_schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_schema_is_itself_valid_draft2020():
    schema = _load_schema()
    Draft202012Validator.check_schema(schema)  # raises if the schema is malformed


def test_schema_version_is_decoupled_from_skill_version():
    schema = _load_schema()
    # sidecar schema version is a data-format version, independent of the skill version
    # (SKILL.md frontmatter).
    sv = schema["properties"]["schema_version"]
    # v1.1 (break-it fix 2026-10-02) added the optional special_category object —
    # a backwards-compatible additive change — so "1.0" documents remain valid.
    assert sv["enum"] == ["1.1", "1.0"]
    assert sv["default"] == "1.1"


def test_special_category_is_optional_and_backwards_compatible():
    schema = _load_schema()
    assert "special_category" not in schema.get("required", [])
    sc = schema["properties"]["special_category"]
    assert sc["type"] == "object"
    assert "involved" in sc["properties"]
    assert "art9_condition" in sc["properties"]


def test_three_step_verdict_enums_present_verbatim():
    schema = _load_schema()
    props = schema["properties"]
    assert props["step1"]["properties"]["verdict"]["enum"] == ["pass", "fail", "requires_refinement"]
    assert props["step2"]["properties"]["verdict"]["enum"] == ["pass", "fail", "requires_scope_reduction"]
    assert props["step3"]["properties"]["verdict"]["enum"] == ["pass", "fail", "pass_with_measures"]
    assert props["overall"]["properties"]["li_appropriate"]["enum"] == ["yes", "no", "conditional"]


def test_validation_findings_use_the_gate_vocabulary():
    schema = _load_schema()
    sev = schema["properties"]["validation"]["properties"]["findings"]["items"] \
               ["properties"]["severity"]
    assert sev["enum"] == ["rejection", "warning", "info"]


def test_domain_gaps_register_is_distinct_from_validation_findings():
    """The sidecar's own gaps[] (unresolved balancing factors) is a separate,
    domain-specific register from validation.findings[] (the validator's own
    diagnostics) — D-WS3-03's split, mirrored here."""
    schema = _load_schema()
    gaps_required = schema["properties"]["gaps"]["items"]["required"]
    findings_required = schema["properties"]["validation"]["properties"]["findings"]["items"]["required"]
    assert gaps_required == ["id", "topic", "question"]
    assert findings_required == ["rule_id", "category", "severity", "message"]
