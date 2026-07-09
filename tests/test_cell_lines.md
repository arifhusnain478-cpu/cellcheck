# Test Cell Lines

The five pre-selected demo lines from the PRD (Success Metrics). Fill in expected values as the
data clients are implemented; use these to verify correctness end-to-end.

| Cell line | RRID | Expected verdict | Note |
| --- | --- | --- | --- |
| HeLa | CVCL_0030 | green | Authentic reference; classic contaminant of *other* lines |
| MCF-7 | CVCL_0031 | green | Authentic breast adenocarcinoma; STR reference |
| MDA-MB-435 | CVCL_0417 | red | Misidentified — actually M14 melanoma, not breast |
| HEK293 | CVCL_0045 | green | Authentic; verify origin (embryonic kidney) |
| MDA-MB-231 | CVCL_0062 | green | Authentic breast adenocarcinoma |

> Verdicts are provisional placeholders — confirm against Cellosaurus + ICLAC once the clients are
> wired up. RRIDs shown are the commonly cited Cellosaurus accessions; verify each during implementation.

## STR fixtures
Place sample STR profiles (paste/CSV/PDF) under [fixtures/](fixtures/) for the STR Test Reader.
