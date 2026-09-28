"""SCHEMA-1 : JSON Schema conformance. Findings-based — never raises."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from ..findings import Finding
from ..registry import rule

SPEC = "references/legitimate-interest-sidecar-schema.json#conformance"


def _schema(ctx) -> dict:
    return json.loads(Path(ctx.schema_path).read_text(encoding="utf-8"))


@rule(id="SCHEMA-1", severity="rejection", category="schema",
      description="Sidecar conforms to legitimate-interest-sidecar-schema.json (Draft 2020-12).",
      spec_anchor=SPEC)
def schema_conformance(sidecar, ctx):
    out = []
    validator = Draft202012Validator(_schema(ctx), format_checker=FormatChecker())
    for err in sorted(validator.iter_errors(sidecar), key=lambda e: list(e.path)):
        out.append(Finding(rule_id="SCHEMA-1", category="schema", severity="rejection",
                           message=f"Schema violation at /{'/'.join(map(str, err.path))}: {err.message}",
                           spec_anchor=SPEC, field="/".join(map(str, err.path)) or None))
    return out
