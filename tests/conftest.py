"""Shared test support for legitimate-interest/tests/.

Makes `lia_validator` importable from tests/ without installing it — mirrors
validate.py's own sys.path.insert(0, HERE) for the validator/ directory.
Also provides ``find_schema``, which resolves a shared portfolio schema
(docs/standards/schemas/) by walking UP from this file's own location. That
works identically in both layouts a skill's bundled tests can run from:

* inside the monorepo, where docs/standards/schemas/ lives at the repo root
  (an ancestor of skills/legitimate-interest/tests/); and
* inside a flat public copy (built by scripts/stage-public-copy.sh), where
  the same schemas are staged at docs/standards/schemas/ relative to the
  public repo root (an ancestor of tests/ there too).
"""
import sys
from pathlib import Path

VALIDATOR_DIR = Path(__file__).resolve().parents[1] / "validator"
if str(VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(VALIDATOR_DIR))


def find_schema(name: str) -> Path:
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "docs" / "standards" / "schemas" / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"schema {name!r} not found in any ancestor of {here} — expected at "
        "docs/standards/schemas/ at the monorepo root or the public repo root"
    )
