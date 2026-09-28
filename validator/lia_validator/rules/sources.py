"""SRC-1 — sources.lock.json manifest coverage and freshness.

Structural mirror of skills/toms-art32/validator/toms_validator/rules/sources.py
(SIX-SKILL-ADOPTION-BRIEF-2026-09-24.md's chosen template) — logic unchanged,
only the module docstring and SPEC anchor differ.

Two independent checks fire under the single SRC-1 id (findings-based; never raise):

- missing-file: a references/**/*.md file exists on disk but sources.lock.json has no
  "references/<relpath>" entry for it.
- staleness: a manifest entry's last_verified is > 365 days before today.

The manifest is loaded from ctx.sources_lock_override if set (fixture testing), else
from <skill-root>/sources.lock.json (ctx.references_dir.parent). A missing or
malformed manifest file emits a finding rather than raising.
"""
import datetime as _dt
import json
from pathlib import Path

from ..findings import Finding
from ..registry import rule

SPEC = "sources.lock.json#freshness"
_STALE_AFTER_DAYS = 365


def _default_manifest_path(ctx) -> Path:
    return ctx.references_dir.parent / "sources.lock.json"


def _validate_shape(manifest, source_desc):
    """A parsed manifest is only usable if it is a JSON object, and its "files" key (when
    present) is itself a JSON object."""
    if not isinstance(manifest, dict):
        return None, f"{source_desc} is not a JSON object (got {type(manifest).__name__})"
    files = manifest.get("files")
    if files is not None and not isinstance(files, dict):
        return None, f"{source_desc}['files'] is not a JSON object (got {type(files).__name__})"
    return manifest, None


def _load_manifest(ctx):
    """Returns (manifest_dict_or_None, error_message_or_None)."""
    override = getattr(ctx, "sources_lock_override", None)
    if override is not None:
        return _validate_shape(override, "ctx.sources_lock_override")
    manifest_path = _default_manifest_path(ctx)
    if not manifest_path.exists():
        return None, f"sources.lock.json not found at {manifest_path}"
    try:
        parsed = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"sources.lock.json at {manifest_path} could not be read/parsed: {exc}"
    return _validate_shape(parsed, str(manifest_path))


def _on_disk_reference_keys(ctx):
    """references/<relpath> keys for every *.md file under ctx.references_dir, recursive."""
    if not ctx.references_dir.exists():
        return set()
    keys = set()
    for path in ctx.references_dir.rglob("*.md"):
        rel = path.relative_to(ctx.references_dir)
        keys.add(f"references/{rel.as_posix()}")
    return keys


@rule(
    id="SRC-1",
    severity="warning",
    category="freshness",
    description="sources.lock.json must declare every on-disk references/**/*.md file, and "
                "every declared entry's last_verified must be within the last 12 months.",
    spec_anchor=SPEC,
)
def source_manifest_coverage_and_freshness(sidecar, ctx):
    out = []
    manifest, error = _load_manifest(ctx)
    if manifest is None:
        out.append(Finding(
            rule_id="SRC-1", category="freshness", severity="warning", priority="high",
            message=f"sources.lock.json could not be loaded: {error}",
            spec_anchor=SPEC,
            fix_hint="Author skills/legitimate-interest/sources.lock.json covering every "
                     "references/**/*.md file.",
        ))
        return out

    declared = set((manifest.get("files") or {}).keys())
    on_disk = _on_disk_reference_keys(ctx)

    for missing in sorted(on_disk - declared):
        out.append(Finding(
            rule_id="SRC-1", category="freshness", severity="warning", priority="high",
            entry_type="reference_file", entry_id=missing, field="files",
            message=f"{missing} exists on disk but has no entry in sources.lock.json.",
            spec_anchor=SPEC,
            fix_hint=f"Add a files['{missing}'] entry to sources.lock.json "
                     "(source_type, jurisdiction, url, last_verified, confidence, owner).",
        ))

    today = _dt.date.today()
    threshold = today - _dt.timedelta(days=_STALE_AFTER_DAYS)
    for path, entry in (manifest.get("files") or {}).items():
        if not isinstance(entry, dict):
            continue
        last_verified = entry.get("last_verified")
        if not isinstance(last_verified, str):
            continue
        try:
            verified_date = _dt.date.fromisoformat(last_verified)
        except ValueError:
            continue
        if verified_date < threshold:
            age_days = (today - verified_date).days
            out.append(Finding(
                rule_id="SRC-1", category="freshness", severity="warning", priority="high",
                entry_type="manifest_entry", entry_id=path, field="last_verified",
                message=(f"sources.lock.json entry '{path}' has last_verified={last_verified} "
                          f"({age_days} days ago, > {_STALE_AFTER_DAYS}-day threshold)."),
                spec_anchor=SPEC,
                fix_hint=f"Re-verify {path} against its source and update sources.lock.json "
                         f"files['{path}'].last_verified.",
            ))

    return out
