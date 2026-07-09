"""Lookup against the ICLAC Register of Misidentified Cell Lines.

The register is bundled locally as data/iclac_register.json (added later).
"""
import json
from pathlib import Path

ICLAC_REGISTER_PATH = Path(__file__).resolve().parent.parent / "data" / "iclac_register.json"


class ICLACService:
    def __init__(self):
        self._register: list | None = None  # loaded lazily

    def _load(self) -> list:
        if self._register is None:
            if ICLAC_REGISTER_PATH.exists():
                self._register = json.loads(ICLAC_REGISTER_PATH.read_text(encoding="utf-8"))
            else:
                self._register = []
        return self._register

    def is_misidentified(self, name: str) -> bool:
        # TODO: normalize and match <name> against known misidentified lines.
        raise NotImplementedError

    def lookup(self, name: str):
        # TODO: return the register entry (true identity, cross-contaminant) or None.
        raise NotImplementedError
