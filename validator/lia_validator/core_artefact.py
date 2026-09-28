"""Project a native legitimate-interest sidecar into the portfolio core artefact.

A PROJECTION, not a rewrite (D-WS3-06): the native sidecar is never modified
or restructured. Structural mirror of toms-art32's adapter
(skills/toms-art32/validator/toms_validator/core_artefact.py) in signature —
`to_core_artefact(sidecar, *, skill_version) -> dict` — but the mapping logic
below is legitimate-interest's own, and (unlike toms-art32's v1.0-era adapter)
this is a NEW 1.1 emitter: subject.type is populated, and sources[]/handoffs[]/
unknowns[] are driven by the sidecar's own content rather than hard-coded empty
(the exact gap SIX-SKILL-ADOPTION-BRIEF-2026-09-24.md calls out).

Field grounding:
  - subject: `assessment.id` if present, else a deterministic slug of
    `assessment.label` (assessment.label is the only field the schema
    requires), else the unmistakable placeholder "unknown-assessment".
    type is always "processing_activity" (skill-artefact-1.1's closed
    enum) — an LIA always assesses a processing activity, never an
    organisation, transfer or freestanding assessment as such.
  - outcome.summary: built from overall.li_appropriate + overall.confidence
    when present, else an honest "no overall verdict recorded" rather than
    a fabricated summary.
  - gaps[]: validation.findings[] (the deterministic validator's OWN
    diagnostics about this document, gate vocabulary), mapped defensively —
    never the sidecar's own domain-specific gaps[] register (unresolved
    balancing factors), which maps to unknowns[] instead (see below). This
    mirrors toms-art32's validation.findings[]/findings[] split (D-WS3-03):
    two different registers, never collapsed into one.
  - sources[]: every entry actually declared in sources.lock.json — for a
    structural-tier LIA the full reference corpus (three-step methodology +
    context modules + case law + jurisdiction notes) is in scope on every
    run, so listing every declared source is honest for "this run", not a
    hard-coded constant (SIX-SKILL-ADOPTION-BRIEF-2026-09-24.md's anti-empty
    rule). Loaded independently of the sidecar so a malformed lock file
    degrades to an empty list rather than crashing the projection.
  - handoffs[]: legitimate-interest's one advertised sibling relationship
    (SKILL.md "Right to Object Response Mode"; data-subject-rights/SKILL.md
    names legitimate-interest for the Art. 21(1) compelling-grounds
    re-assessment) is INBOUND — data-subject-rights consumes this skill's
    result, not the other way round. Per the brief: emit a handoffs[] entry
    naming data-subject-rights whenever this run's overall verdict could
    support that re-assessment (li_appropriate in {yes, conditional}); a
    'no' verdict means Art. 6(1)(f) was never available, so there is nothing
    for an Art. 21(1) re-balancing to build on.
  - unknowns[]: the sidecar's own gaps[] register (unresolved balancing
    factors) — genuinely open questions about the assessment's substance,
    with no sibling skill to hand them to, so they surface as unknowns[]
    rather than handoffs[] (brief: "when it's an open question with no
    sibling data available, emit unknowns[]").
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ARTEFACT_SCHEMA_VERSION = "1.1"
SKILL_NAME = "legitimate-interest"
HANDOFF_SIBLING = "data-subject-rights"

# Loose RFC3339 date-time shape check — good enough to decide "is this worth
# passing through" without re-implementing jsonschema's FormatChecker here.
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

_OUTCOME_BY_VALIDATION_STATUS = {
    "passed": "complete",
    "passed_with_warnings": "provisional",
    "failed": "blocked",
}

_UNKNOWN_ASSESSMENT_ID = "unknown-assessment"

# skills/legitimate-interest/validator/lia_validator/core_artefact.py -> skill root
_SKILL_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SOURCES_LOCK = _SKILL_ROOT / "sources.lock.json"


def _slugify(value: str) -> str:
    """Deterministic: the same assessment label always yields the same slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or _UNKNOWN_ASSESSMENT_ID


def _now_iso() -> str:
    """Same timestamp shape the runner stamps onto Result.validated_at."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _generated_at(sidecar: dict) -> str:
    """The sidecar's own `generated_at` is untrusted input: a malformed sidecar can
    carry `null`, a number, or anything else JSON allows there. Fall back to the
    current UTC time in the same shape the rest of this validator stamps, rather
    than ever copying a non-string or malformed value through."""
    value = sidecar.get("generated_at")
    if isinstance(value, str) and _DATETIME_RE.match(value):
        return value
    return _now_iso()


def _subject(sidecar: dict) -> dict:
    assessment = sidecar.get("assessment")
    if not isinstance(assessment, dict):
        assessment = {}
    aid = assessment.get("id")
    label = assessment.get("label")
    if isinstance(aid, str) and aid:
        subject_id = aid
    elif isinstance(label, str) and label:
        subject_id = _slugify(label)
    else:
        subject_id = _UNKNOWN_ASSESSMENT_ID
    return {
        "id": subject_id,
        "label": label if isinstance(label, str) and label else (
            aid if isinstance(aid, str) and aid else "unknown processing activity"),
        "type": "processing_activity",
    }


def _outcome_summary(sidecar: dict) -> str:
    overall = sidecar.get("overall")
    if not isinstance(overall, dict):
        return "no overall verdict recorded"
    li = overall.get("li_appropriate")
    if li not in ("yes", "no", "conditional"):
        return "no overall verdict recorded"
    confidence = overall.get("confidence")
    if isinstance(confidence, str) and confidence:
        return f"Art. 6(1)(f) appropriate: {li} (confidence: {confidence})"
    return f"Art. 6(1)(f) appropriate: {li}"


def _gap(f: dict) -> dict:
    """A single validation.findings[] entry, defensively read."""
    return {
        "id": f.get("entry_id") or f.get("rule_id") or "gap",
        "severity": f.get("severity") if f.get("severity") in ("rejection", "warning", "info") else "rejection",
        "message": f.get("message") or "(no message on this finding)",
    }


def _load_sources_lock(path: Path) -> dict:
    """Defensive load: a missing or malformed lock file degrades to {} rather
    than crashing the projection — the adapter must never raise (mirrors the
    per-rule and per-run guards in runner.py)."""
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _sources(sources_lock_path: Optional[Path]) -> list:
    manifest = _load_sources_lock(sources_lock_path or _DEFAULT_SOURCES_LOCK)
    files = manifest.get("files")
    if not isinstance(files, dict):
        return []
    out = []
    for relpath, entry in files.items():
        if not isinstance(entry, dict):
            continue
        last_verified = entry.get("last_verified")
        if not isinstance(last_verified, str):
            continue
        citation = entry.get("notes") or entry.get("url") or relpath
        out.append({
            "id": relpath,
            "citation": citation,
            "last_verified": last_verified,
        })
    return out


def _handoffs(sidecar: dict) -> list:
    overall = sidecar.get("overall")
    li = overall.get("li_appropriate") if isinstance(overall, dict) else None
    if li not in ("yes", "conditional"):
        return []
    return [{
        "sibling_skill": HANDOFF_SIBLING,
        "reason": (f"This LIA's overall verdict (li_appropriate: {li}) is the balance "
                   "data-subject-rights needs when re-assessing a subsequent Art. 21(1) "
                   "objection under the higher 'compelling legitimate grounds' threshold."),
    }]


def _unknowns(sidecar: dict) -> list:
    gaps = sidecar.get("gaps")
    if not isinstance(gaps, list):
        return []
    out = []
    for g in gaps:
        if not isinstance(g, dict):
            continue
        out.append({
            "id": g.get("id") or "gap",
            "question": g.get("question") or g.get("topic") or
                        "(unresolved balancing factor, no question recorded)",
            "blocking": g.get("severity") == "rejection",
        })
    return out


def to_core_artefact(sidecar: dict, *, skill_version: str,
                      sources_lock_path: Optional[Path] = None) -> dict:
    validation = sidecar.get("validation")
    if not isinstance(validation, dict):
        validation = {}
    validation_findings = validation.get("findings")
    if not isinstance(validation_findings, list):
        validation_findings = []
    return {
        "artefact_schema_version": ARTEFACT_SCHEMA_VERSION,
        "skill": SKILL_NAME,
        "skill_version": skill_version,
        "generated_at": _generated_at(sidecar),
        "subject": _subject(sidecar),
        "outcome": {
            "status": _OUTCOME_BY_VALIDATION_STATUS.get(
                validation.get("status", "passed"), "provisional"),
            "summary": _outcome_summary(sidecar),
        },
        "gaps": [_gap(f) for f in validation_findings if isinstance(f, dict)],
        "sources": _sources(sources_lock_path),
        "handoffs": _handoffs(sidecar),
        "unknowns": _unknowns(sidecar),
    }


def blocked_artefact(*, skill_version: str, reason: str) -> dict:
    """Minimal, always schema-valid artefact for when `to_core_artefact` itself
    raises despite the guards above (defence in depth — mirrors
    lia_validator.runner.validate()'s per-rule exception handler)."""
    return {
        "artefact_schema_version": ARTEFACT_SCHEMA_VERSION,
        "skill": SKILL_NAME,
        "skill_version": skill_version,
        "generated_at": _now_iso(),
        "subject": {"id": _UNKNOWN_ASSESSMENT_ID, "label": "unknown processing activity",
                    "type": "processing_activity"},
        "outcome": {
            "status": "blocked",
            "summary": f"Core artefact adapter failed: {reason}",
        },
        "gaps": [{
            "id": "core-artefact-adapter-error",
            "severity": "rejection",
            "message": f"to_core_artefact raised: {reason}",
        }],
        "sources": [],
        "handoffs": [],
        "unknowns": [],
    }
