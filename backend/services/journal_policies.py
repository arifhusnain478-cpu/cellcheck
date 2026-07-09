"""Static reference for journal cell-line reporting requirements.

Small, deliberately-simple starter set covering the demo journals, with an
ANSI/ATCC (ASN-0002)-style generic fallback for anything unlisted. `required_fields`
are MethodsRequest field names used for the compliance check.
"""
from typing import Optional

from pydantic import BaseModel

from models.methods import MethodsRequest

# form field -> human-readable label (for missing-field messages)
FIELD_LABELS = {
    "source": "source / catalog number",
    "authentication_service": "authentication method (e.g. STR service)",
    "authentication_date": "authentication date",
    "mycoplasma_test_date": "mycoplasma test date",
    "passage_range": "passage range",
}


class JournalPolicy(BaseModel):
    name: str
    listed: bool = True            # False = generic fallback (journal not on our list)
    required_fields: list[str] = []
    note: str = ""


_GENERIC = JournalPolicy(
    name="Generic (ANSI/ATCC ASN-0002)",
    listed=False,
    required_fields=["source", "authentication_service", "authentication_date",
                     "mycoplasma_test_date", "passage_range"],
    note="No specific policy on file for this journal — applying ANSI/ATCC ASN-0002-style reporting.",
)

# keyed by a lowercase substring to match against the user's target_journal
_POLICIES: dict[str, JournalPolicy] = {
    "cancer research": JournalPolicy(
        name="Cancer Research (AACR)",
        required_fields=["source", "authentication_service", "authentication_date",
                         "mycoplasma_test_date", "passage_range"],
        note="AACR requires STR authentication (and how recently it was performed), "
             "mycoplasma testing, and source.",
    ),
    "nature": JournalPolicy(
        name="Nature",
        required_fields=["source", "authentication_service", "authentication_date",
                         "mycoplasma_test_date"],
        note="Nature requires the cell line source, authentication method, and mycoplasma status.",
    ),
    "cell": JournalPolicy(
        name="Cell (Cell Press)",
        required_fields=["source", "authentication_service", "authentication_date",
                         "mycoplasma_test_date"],
        note="Cell Press STAR Methods requires source, authentication, and mycoplasma testing.",
    ),
    "science": JournalPolicy(
        name="Science",
        required_fields=["source", "authentication_service", "mycoplasma_test_date"],
        note="Science requires cell line authentication and mycoplasma testing.",
    ),
    "plos one": JournalPolicy(
        name="PLOS ONE",
        required_fields=["source", "authentication_service"],
        note="PLOS ONE requires the source and authentication; RRID citation is recommended.",
    ),
}


def resolve_policy(journal: Optional[str]) -> JournalPolicy:
    """Match a journal name to a known policy, else the generic fallback."""
    if not journal:
        return _GENERIC
    q = journal.strip().lower()
    # check longer keys first so "cancer research" isn't shadowed by a shorter match
    for key in sorted(_POLICIES, key=len, reverse=True):
        if key in q:
            return _POLICIES[key]
    return _GENERIC


def missing_field_labels(req: MethodsRequest, policy: JournalPolicy) -> list[str]:
    """Human-readable labels for the policy's required fields left blank in the form."""
    values = {
        "source": req.source,
        "authentication_service": req.authentication_service,
        "authentication_date": req.authentication_date,
        "mycoplasma_test_date": req.mycoplasma_test_date,
        "passage_range": req.passage_range,
    }
    return [FIELD_LABELS[f] for f in policy.required_fields if not (values.get(f) or "").strip()]
