"""CLI fail-closed guard — break-it test 2026-10-02.

Before this fix, validate.py's file-read step (`json.loads(args.sidecar.read_text(...))`)
had no guard at all: a missing file, an unreadable file, invalid UTF-8, or invalid JSON
syntax raised an uncaught exception and printed a raw Python traceback. A non-object
top-level JSON document (an array, a string, a number, null) passed the bare
`json.loads()` call but then crashed differently — with `--emit-core-artefact`, the
`{**sidecar, ...}` dict-spread raised TypeError because `sidecar` was not a mapping.

Probes proving each case: scratchpad/breakit/legitimate-interest/p8_invalid_json.json,
p9_toplevel_array.json, p10_toplevel_string.json, p11_toplevel_null.json (adapted here
as committed fixtures per FIX-BRIEF 2026-10-02 — never referencing the scratchpad path
from committed code).

Every case must now: (1) print a clean one-line message, never a traceback, (2) exit 1,
(3) report status "failed" with exactly one rejection finding (INPUT-1), consistent
with the runner's own RUNNER-0 fail-closed shape, and (4) with --emit-core-artefact,
still write a schema-valid, blocked artefact rather than skipping the flag or crashing.
"""
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATE = REPO_ROOT / "skills" / "legitimate-interest" / "validator" / "validate.py"
ARTEFACT_SCHEMA = json.loads(
    (REPO_ROOT / "docs" / "standards" / "schemas"
     / "skill-artefact-1.1.schema.json").read_text(encoding="utf-8"))


def run_cli(*argv):
    return subprocess.run(
        [sys.executable, str(VALIDATE), *map(str, argv)],
        capture_output=True, text=True)


def _assert_clean_failure(proc):
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stdout
    assert "Traceback" not in proc.stderr


def test_missing_file_fails_closed(tmp_path):
    missing = tmp_path / "does-not-exist.json"
    proc = run_cli(missing, "--format", "json")
    _assert_clean_failure(proc)
    envelope = json.loads(proc.stdout)
    assert envelope["status"] == "failed"
    assert [f["rule_id"] for f in envelope["findings"]] == ["INPUT-1"]


def test_unreadable_file_fails_closed(tmp_path):
    unreadable = tmp_path / "no-permission.json"
    unreadable.write_text("{}", encoding="utf-8")
    unreadable.chmod(0o000)
    try:
        proc = run_cli(unreadable, "--format", "json")
        _assert_clean_failure(proc)
        envelope = json.loads(proc.stdout)
        assert envelope["status"] == "failed"
        assert [f["rule_id"] for f in envelope["findings"]] == ["INPUT-1"]
    finally:
        unreadable.chmod(0o644)  # restore so tmp_path cleanup can remove it


def test_invalid_utf8_fails_closed(tmp_path):
    bad_bytes = tmp_path / "bad-utf8.json"
    bad_bytes.write_bytes(b'{"schema_version": "\xff\xfe invalid utf-8"}')
    proc = run_cli(bad_bytes, "--format", "json")
    _assert_clean_failure(proc)
    envelope = json.loads(proc.stdout)
    assert envelope["status"] == "failed"
    assert [f["rule_id"] for f in envelope["findings"]] == ["INPUT-1"]


def test_invalid_json_syntax_fails_closed(tmp_path):
    # Mirrors scratchpad/breakit/legitimate-interest/p8_invalid_json.json
    bad_json = tmp_path / "invalid.json"
    bad_json.write_text('{\n  "schema_version": "1.0",\n  "generated_by": "x",\n',
                         encoding="utf-8")
    proc = run_cli(bad_json, "--format", "json")
    _assert_clean_failure(proc)
    envelope = json.loads(proc.stdout)
    assert envelope["status"] == "failed"
    assert [f["rule_id"] for f in envelope["findings"]] == ["INPUT-1"]


@pytest.mark.parametrize("name,content", [
    # Mirrors p9_toplevel_array.json / p10_toplevel_string.json / p11_toplevel_null.json
    ("array", '["not", "an", "object"]'),
    ("string", '"just a string"'),
    ("null", "null"),
    ("number", "42"),
])
def test_non_object_top_level_json_fails_closed_instead_of_crashing(tmp_path, name, content):
    path = tmp_path / f"toplevel-{name}.json"
    path.write_text(content, encoding="utf-8")
    proc = run_cli(path, "--format", "json")
    _assert_clean_failure(proc)
    envelope = json.loads(proc.stdout)
    assert envelope["status"] == "failed"
    assert [f["rule_id"] for f in envelope["findings"]] == ["INPUT-1"]


@pytest.mark.parametrize("name,content", [
    ("array", '["not", "an", "object"]'),
    ("string", '"just a string"'),
    ("null", "null"),
    ("missing", None),
    ("invalid-json", '{\n  "oops"'),
])
def test_emit_core_artefact_still_writes_a_blocked_schema_valid_artefact_on_bad_input(
        tmp_path, name, content):
    if content is None:
        path = tmp_path / "does-not-exist.json"
    else:
        path = tmp_path / f"bad-{name}.json"
        path.write_text(content, encoding="utf-8")
    out = tmp_path / "core.json"
    proc = run_cli(path, "--emit-core-artefact", out, "--format", "json")
    _assert_clean_failure(proc)
    assert out.exists(), f"no artefact written for {name}; stderr={proc.stderr}"
    artefact = json.loads(out.read_text(encoding="utf-8"))
    jsonschema.validate(artefact, ARTEFACT_SCHEMA, format_checker=jsonschema.FormatChecker())
    assert artefact["outcome"]["status"] == "blocked"


def test_human_format_bad_input_also_fails_closed_with_no_traceback(tmp_path):
    missing = tmp_path / "does-not-exist.json"
    proc = run_cli(missing)
    _assert_clean_failure(proc)
    assert "status: failed" in proc.stdout
    assert "INPUT-1" in proc.stdout
