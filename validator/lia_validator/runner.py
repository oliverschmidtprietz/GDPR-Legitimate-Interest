"""Runner — orchestrates rule evaluation.

Importing this module does NOT populate the rule registry — importing the
``lia_validator.rules`` package does (its __init__ imports every rule module).
validate() guards against an empty registry by failing closed (RUNNER-0): a
zero-rule run must never return a green result for arbitrary input.

Structural mirror of skills/toms-art32/validator/toms_validator/runner.py
(SIX-SKILL-ADOPTION-BRIEF-2026-09-24.md's chosen template).
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .findings import Finding
from .registry import RULES

# VALIDATOR_VERSION is the validator TOOL's own version, independent of the skill version
# (SKILL.md frontmatter) and of the sidecar data-format version (schema_version "1.0"). It is
# stamped into every Result so a findings report is traceable to the tool build that produced
# it, and it moves on its own cadence — bumping the skill's vX.Y does not bump this, and vice
# versa. (It is the one place a three-part number is used, by convention for a code artefact;
# the skill itself follows the repo's two-digit vX.Y SemLite.)
VALIDATOR_VERSION = "v0.1.0"
REPORT_SCHEMA_VERSION = "2.0"   # portfolio findings-report format (docs/standards/)
SKILL_NAME = "legitimate-interest"
_BLOCKING = {"rejection"}


@dataclass(frozen=True)
class Context:
    mode: str                     # "internal" | "submission"
    schema_path: Path
    references_dir: Path
    sources_lock_override: Optional[dict] = None   # fixture testing (mirrors toms-art32/ropa)


@dataclass
class Result:
    status: str
    summary: dict
    findings: List[Finding]
    validator_version: str = VALIDATOR_VERSION
    report_schema_version: str = REPORT_SCHEMA_VERSION
    mode: str = "internal"
    artefact_path: str = ""
    validated_at: str = ""


def validate(sidecar: dict, ctx: Context, rule_filter: Optional[set] = None) -> Result:
    findings: List[Finding] = []
    if not RULES:
        # Fail closed: an empty registry means the rules package was never imported —
        # every check would silently be skipped and any input would pass.
        findings.append(Finding(
            rule_id="RUNNER-0", category="runner", severity="rejection",
            message="No rules are registered — the rule registry is empty, so nothing was "
                    "actually validated. Import lia_validator.rules (the package __init__ "
                    "populates the registry) before calling validate(); importing "
                    "lia_validator.runner alone does not.",
            spec_anchor="validator/README.md",
            fix_hint="Add `import lia_validator.rules` (or use validate.py, which does this) "
                     "before calling validate().",
        ))
        return Result(status="failed",
                      summary={"rejections": 1, "warnings": 0, "info": 0,
                               "rules_evaluated": 0},
                      findings=findings,
                      mode=ctx.mode,
                      validated_at=datetime.now(timezone.utc)
                          .isoformat(timespec="seconds").replace("+00:00", "Z"))
    rules_evaluated = 0
    for rid, (spec, fn) in RULES.items():
        if rule_filter and rid not in rule_filter:
            continue
        rules_evaluated += 1
        try:
            findings.extend(fn(sidecar, ctx) or [])     # rules RETURN findings, never raise
        except Exception as exc:  # a rule must never crash the run
            findings.append(Finding(
                rule_id=rid, category=spec.category, severity="rejection",
                message=f"Rule {rid} raised {type(exc).__name__}: {exc}",
                spec_anchor=spec.spec_anchor,
                fix_hint="Internal: a rule raised on this input; the data likely violates a "
                         "structural assumption reported by SCHEMA-1.",
            ))
    has_rejection = any(f.severity in _BLOCKING for f in findings)
    has_warning = any(f.severity == "warning" for f in findings)
    status = "failed" if has_rejection else ("passed_with_warnings" if has_warning else "passed")
    summary = {
        "rejections": sum(1 for f in findings if f.severity == "rejection"),
        "warnings": sum(1 for f in findings if f.severity == "warning"),
        "info": sum(1 for f in findings if f.severity == "info"),
        "rules_evaluated": rules_evaluated,
    }
    return Result(
        status=status,
        summary=summary,
        findings=findings,
        mode=ctx.mode,
        validated_at=datetime.now(timezone.utc)
            .isoformat(timespec="seconds").replace("+00:00", "Z"),
    )


def to_findings_json(result: Result, *, skill_version: str) -> dict:
    """Serialize a Result into the portfolio findings-report 2.0 envelope."""
    return {
        "report_schema_version": result.report_schema_version,
        "status": result.status,
        "skill": SKILL_NAME,
        "skill_version": skill_version,
        "validator_version": result.validator_version,
        "validated_at": result.validated_at,
        "artefact_path": result.artefact_path,
        "mode": result.mode,
        "summary": result.summary,
        "findings": [f.to_dict() for f in result.findings],
    }
