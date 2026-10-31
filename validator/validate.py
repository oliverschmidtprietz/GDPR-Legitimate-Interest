#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["jsonschema>=4.21"]
# ///
"""legitimate-interest validator CLI — v0.1.0.

  uv run skills/legitimate-interest/validator/validate.py <lia-sidecar.json> [--mode internal|submission] [--format human|json]
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lia_validator.runner import validate, Context, Result, to_findings_json  # noqa: E402
from lia_validator.findings import Finding  # noqa: E402
from lia_validator.core_artefact import to_core_artefact, blocked_artefact  # noqa: E402
from lia_validator import rules  # noqa: E402,F401  (populates the registry)

DEFAULT_SCHEMA = HERE.parent / "references" / "legitimate-interest-sidecar-schema.json"
DEFAULT_REFS = HERE.parent / "references"


def _skill_version() -> str:
    """Read the live version from SKILL.md frontmatter — never hard-code it (CLAUDE.md)."""
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    for line in skill_md.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version:"):
            return line.split(":", 1)[1].strip()
    raise SystemExit("SKILL.md has no version: field")


def main(argv=None):
    p = argparse.ArgumentParser(prog="lia-validator")
    p.add_argument("sidecar", type=Path)
    p.add_argument("--mode", choices=["internal", "submission"], default="internal")
    p.add_argument("--format", choices=["human", "json"], default="human")
    p.add_argument("--schema-path", type=Path, default=DEFAULT_SCHEMA)
    p.add_argument("--references-dir", type=Path, default=DEFAULT_REFS)
    p.add_argument(
        "--emit-core-artefact",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "After validation, write the portfolio core artefact "
            "(skill-artefact-1.1 schema) projection of THIS run's result to PATH. "
            "Built from the live validation result, never the sidecar's "
            "embedded validation block. Report and exit code unchanged."
        ),
    )
    args = p.parse_args(argv)

    input_error = None  # set to a one-line message on any bad-input failure below
    sidecar = None

    try:
        raw_text = args.sidecar.read_text(encoding="utf-8")
    except FileNotFoundError:
        input_error = f"sidecar not found: {args.sidecar}"
    except IsADirectoryError:
        input_error = f"sidecar path is a directory, not a file: {args.sidecar}"
    except UnicodeDecodeError as exc:
        input_error = f"sidecar is not valid UTF-8: {args.sidecar}: {exc}"
    except OSError as exc:
        input_error = f"could not read sidecar {args.sidecar}: {exc}"

    if input_error is None:
        try:
            sidecar = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            input_error = f"malformed JSON in {args.sidecar}: {exc}"

    if input_error is None and not isinstance(sidecar, dict):
        input_error = (f"{args.sidecar} does not contain a JSON object at its top level "
                       f"(got {type(sidecar).__name__}) — a sidecar must be a JSON object.")

    if input_error is not None:
        # Fail closed, no traceback: a bad-input run is reported exactly like any other
        # failed validation (RUNNER-0's shape) rather than crashing with a raw exception.
        result = Result(
            status="failed",
            summary={"rejections": 1, "warnings": 0, "info": 0, "rules_evaluated": 0},
            findings=[Finding(
                rule_id="INPUT-1", category="input", severity="rejection",
                message=f"Could not validate: {input_error}",
                spec_anchor="validator/README.md",
                fix_hint="Fix the sidecar path/encoding/JSON syntax and re-run.",
            )],
            mode=args.mode,
            artefact_path=str(args.sidecar),
            validated_at=datetime.now(timezone.utc)
                .isoformat(timespec="seconds").replace("+00:00", "Z"),
        )
        if args.emit_core_artefact is not None:
            artefact = blocked_artefact(skill_version=_skill_version(), reason=input_error)
            args.emit_core_artefact.write_text(
                json.dumps(artefact, indent=2) + "\n", encoding="utf-8")
        if args.format == "json":
            print(json.dumps(to_findings_json(result, skill_version=_skill_version()), indent=2))
        else:
            print(f"status: {result.status}  ({len(result.findings)} findings)")
            for f in result.findings:
                print(f"  [{f.severity}] {f.rule_id}: {f.message}")
        return 1

    ctx = Context(mode=args.mode, schema_path=args.schema_path, references_dir=args.references_dir)
    result = validate(sidecar, ctx)
    result.artefact_path = str(args.sidecar)

    if args.emit_core_artefact is not None:
        live_sidecar = {**sidecar, "validation": {
            "status": result.status,
            "findings": [f.to_dict() for f in result.findings],
        }}
        try:
            artefact = to_core_artefact(live_sidecar,
                                        skill_version=_skill_version())
        except Exception as exc:  # adapter must never crash the run, mirrors
            # runner.validate()'s per-rule guard: the report on stdout and the
            # exit code stay exactly as they would be without this flag, and a
            # minimal, schema-valid, blocked artefact is written instead of a
            # traceback (docs/standards/PORTFOLIO-STANDARD.md ~line 129).
            artefact = blocked_artefact(
                skill_version=_skill_version(),
                reason=f"{type(exc).__name__}: {exc}")
        args.emit_core_artefact.write_text(
            json.dumps(artefact, indent=2) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(to_findings_json(result, skill_version=_skill_version()), indent=2))
    else:
        print(f"status: {result.status}  ({len(result.findings)} findings)")
        for f in result.findings:
            print(f"  [{f.severity}] {f.rule_id}: {f.message}")
    return 1 if result.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
