"""Make `lia_validator` importable from tests/ without installing it —
mirrors validate.py's own sys.path.insert(0, HERE) for the validator/ directory.
"""
import sys
from pathlib import Path

VALIDATOR_DIR = Path(__file__).resolve().parents[1] / "validator"
if str(VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(VALIDATOR_DIR))
