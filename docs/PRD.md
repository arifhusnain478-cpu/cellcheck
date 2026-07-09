# CellCheck — Product Requirements Document

**Hackathon:** Built with Claude: Life Sciences
**Track:** Builder
**Deadline:** July 13, 2026, 9:00 PM ET (July 14, ~6:00 AM Pakistan time)
**Builder:** Hunain Arif (solo)

---

## 1. Executive Summary

CellCheck is an AI-native cell line authentication workflow tool. It helps biomedical researchers instantly check whether the cell lines they use are genuine, contaminated, or misidentified — a problem that affects 15-20% of cell lines used in research worldwide. CellCheck compresses a process that normally takes weeks of confusion into a guided workflow that takes minutes, and generates publication-ready documentation at the end.

---

## 2. Problem Statement

- **15-20%** of cell lines used in biomedical research globally are misidentified or cross-contaminated.
- **464** cell lines are confirmed misidentified/contaminated in the ICLAC register.
- **52%** of researchers never authenticate their cell lines. **74%** never run STR profiling (the gold-standard test).
- Barriers: cost (61% cite this), time (53%), and research delays (35%).
- Estimated **$700 million/year** in research funding is at risk due to bad cell lines.
- Real consequence: thousands of retracted papers, failed drug trials, and derailed careers (e.g., MDA-MB-435, believed to be breast cancer for 25+ years, was actually melanoma).
- Journals (Nature, Cell, Science, Cancer Research) increasingly *require* authentication statements and RRIDs — but researchers have no easy way to comply.

**Core insight:** The tools to catch this problem already exist (Cellosaurus, ICLAC, STR profiling). The barrier isn't technology — it's a broken, confusing workflow around that technology.

---

## 3. Target User

**Primary persona: Sarah, PhD student / postdoc in a wet lab**

- Works with 3-10 cell lines across her research
- Under pressure from her PI or a journal deadline to authenticate her cells
- Has little to no bioinformatics training
- Doesn't know where to start, what a "good" STR result looks like, or how to write a compliant methods section
- Wants a fast, trustworthy answer — not a research project just to check her cells

**Secondary personas:**
- PI managing a lab's full inventory of cell lines
- Core facility manager doing routine QC
- Journal-facing researcher preparing a manuscript for submission

---

## 4. Solution Overview — Three Modes

### Mode 1: Quick Check
User enters a cell line name, catalog number, or RRID. Gets back:
- Traffic-light verdict (green / yellow / red)
- True identity (correct name, RRID, origin, species, synonyms)
- Retracted/corrected papers associated with misidentification of this line
- Recommended next steps

### Mode 2: STR Test Reader
User uploads or pastes their STR profiling results (16-24 loci). Gets back:
- Match verdict against Cellosaurus reference profiles (via CLASTR)
- Plain-language interpretation (confirmed match / drift / contamination suspected)
- Recommended actions based on result

### Mode 3: Methods Section Generator
User fills a short form (cell line, source, authentication date/service, passage range, target journal). Gets back:
- A publication-ready methods paragraph with correct RRID citation
- Journal-compliance check against known cell line reporting policies

---

## 5. Feature Requirements

### 5.1 Quick Check

| Requirement | Detail |
|---|---|
| Input | Free-text search: cell line name, catalog number, or RRID |
| Data sources | Cellosaurus (identity), ICLAC (misidentification status), Semantic Scholar (retractions) |
| Output fields | `verdict` (green/yellow/red), `identity` (name, RRID, origin, species, synonyms), `retractions` (list of papers), `next_steps` (list of recommended actions) |
| Reasoning layer | Claude synthesizes raw data into a plain-language verdict summary |
| Edge case | Cell line not found in Cellosaurus → return "unknown line" state with guidance to verify spelling or check manually |
| Success criteria | Returns full result in under 5 seconds for cached lines; under 10 seconds for live queries |

### 5.2 STR Test Reader

| Requirement | Detail |
|---|---|
| Input | Pasted STR data (locus: allele pairs) or uploaded file (PDF/CSV/text) |
| Data sources | CLASTR algorithm (via Cellosaurus), Cellosaurus reference profiles |
| Output fields | `match_percentage`, `matched_line`, `interpretation` (plain language), `anomalies` (list), `recommendation` |
| Reasoning layer | Claude explains match/mismatch in plain language, distinguishes drift from contamination |
| Edge case | Malformed/incomplete STR data → clear error message with format example |
| Success criteria | Correctly identifies known reference profiles (HeLa, MCF-7, etc.) with >90% confidence in test cases |

### 5.3 Methods Section Generator

| Requirement | Detail |
|---|---|
| Input | Form: cell line name, source/catalog, authentication date, authentication service, passage range, target journal |
| Data sources | RRID from Cellosaurus, journal policy reference (static list for v1: Nature, Cell, Science, Cancer Research, PLOS ONE) |
| Output fields | `methods_paragraph` (text), `compliance_status` (per-journal checklist) |
| Reasoning layer | Claude generates the paragraph in correct academic style, cites RRID correctly |
| Edge case | Target journal not in known list → generate generic ANSI/ATCC-compliant paragraph |
| Success criteria | Output paragraph requires zero manual editing for correctness (RRID, dates, journal tone) |

---

## 6. Data Sources & Dependencies

| # | Source | Role | Access |
|---|---|---|---|
| 1 | **Cellosaurus** | True cell line identity, RRID, synonyms, provenance | Free REST API |
| 2 | **ICLAC Register** | Known misidentified/contaminated cell lines | Free, downloadable dataset |
| 3 | **CLASTR** | STR profile matching algorithm | Free, via Cellosaurus/Expasy |
| 4 | **Semantic Scholar** | Retracted/corrected paper lookup | Free REST API |
| 5 | **RRID System** | Standardized citation IDs | Bundled in Cellosaurus data |
| 6 | **Claude API** | Reasoning, explanation, generation layer | Hackathon $200 credit + Claude Max |

---

## 7. Technical Architecture

```
[React/Vite Frontend] 
       │ (fetch/axios)
       ▼
[FastAPI Backend]
       ├──> services/cellosaurus_client.py   → Cellosaurus API
       ├──> services/iclac_service.py         → Local ICLAC dataset
       ├──> services/clastr_client.py         → CLASTR matching
       ├──> services/semantic_scholar_client.py → Semantic Scholar API
       └──> services/llm_client.py            → LLM API (Anthropic default, Groq as configurable fallback)
```

- **Backend:** FastAPI (Python), deployed to HuggingFace Spaces (Docker mode)
- **Frontend:** React + Vite, shadcn/ui + Tailwind CSS, deployed to Vercel
- **Caching:** In-memory cache during session; pre-cached JSON for demo cell lines
- **No database, no user accounts in v1** — stateless requests only

---

## 8. UI/UX Requirements

- Clean, minimal design — warm neutral palette (off-white/cream base, one accent color), traffic-light colors reserved only for verdicts
- Single search box as the primary entry point (Quick Check is the default landing view)
- Tab or nav-based switching between the 3 modes
- Mobile-responsive (max content width ~800px)
- Every claim in the UI must show its source (e.g., "via Cellosaurus", "via ICLAC") — builds trust with scientific users
- Copy-to-clipboard and download options wherever generated text appears (methods paragraph)

---

## 9. Non-Goals (v1)

- No wet-lab automation or physical test ordering integration
- No user accounts, login, or saved history
- No batch upload of multiple cell lines at once
- No support for non-English methods sections
- No antibody, plasmid, or mouse-strain authentication (cell lines only)
- No diagnosis or treatment recommendations (research tool only, not clinical)

---

## 10. Success Metrics (Hackathon Context)

- All 3 modes functioning end-to-end on a live deployed URL
- Correct, verifiable results for 5 pre-selected test cell lines (HeLa, MCF-7, MDA-MB-435, HEK293, MDA-MB-231)
- Demo video under 3 minutes, tells a clear before/after story
- Every factual claim in the demo traceable to a real source (no hallucinated data)

---

## 11. Timeline & Milestones

See separate `CHECKPOINTS.md` for the full day-by-day breakdown.

---

## 12. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| External API downtime during demo | Pre-cache all demo cell line responses locally |
| STR Test Reader too complex to finish | Vertical slice approach — Quick Check ships first and stands alone if needed |
| Claude hallucinating biology facts | Ground every Claude call in retrieved data; never let Claude answer from memory alone |
| Deployment issues late in timeline | Deploy early (Day 2), not on the last day |
| Running out of time for demo video | Hard cutoff: stop building by end of Day 3, dedicate remaining time fully to demo |

---

## 13. Future Roadmap (Post-Hackathon, v2+)

- Batch upload for full lab inventory audits
- Antibody validation (parallel problem, same architecture)
- Lab-wide dashboards for PIs
- Integration with ELN platforms (Benchling, LabArchives)
- Multi-language methods section support

---

# API Contract

Base URL (local dev): `http://localhost:8000`
Base URL (production): TBD after HuggingFace Spaces deployment

All responses are JSON. All errors follow the standard error shape at the bottom.

---

## POST `/api/cellcheck/quick`

**Purpose:** Quick Check — search a cell line and get identity, verdict, and retractions.

**Request body:**
```json
{
  "query": "MDA-MB-435"
}
```

**Response (200 OK):**
```json
{
  "query": "MDA-MB-435",
  "verdict": "red",
  "identity": {
    "correct_name": "MDA-MB-435",
    "rrid": "CVCL_0417",
    "true_origin": "Melanoma (M14 origin), reclassified from breast adenocarcinoma",
    "species": "Homo sapiens",
    "synonyms": ["MDAMB435", "MDA MB 435", "MDA-MB435S"],
    "source_lab": "MD Anderson Cancer Center, 1976"
  },
  "retractions": [
    {
      "title": "Example retracted paper title",
      "journal": "Cancer Research",
      "year": 2021,
      "reason": "Cell line identity error",
      "url": "https://..."
    }
  ],
  "next_steps": [
    "Order STR profiling before publication",
    "Check mycoplasma status",
    "Review passage history"
  ],
  "sources": ["cellosaurus", "iclac", "semantic_scholar"]
}
```

**Error cases:**
- `404` — Cell line not found in Cellosaurus
- `503` — One or more upstream data sources unavailable (partial results returned if possible)

---

## POST `/api/cellcheck/str-analysis`

**Purpose:** STR Test Reader — interpret uploaded STR profile data.

**Request body:**
```json
{
  "claimed_identity": "MCF-7",
  "str_profile": {
    "D5S818": ["11", "12"],
    "D13S317": ["11", "11"],
    "D7S820": ["8", "9"],
    "D16S539": ["11", "12"],
    "vWA": ["16", "17"],
    "TH01": ["6", "9.3"],
    "Amelogenin": ["X", "X"]
  }
}
```

**Response (200 OK):**
```json
{
  "match_verdict": "green",
  "match_percentage": 97,
  "matched_line": {
    "name": "MCF-7",
    "rrid": "CVCL_0031"
  },
  "loci_analysis": {
    "total_loci": 16,
    "matching_loci": 15,
    "anomalous_loci": ["D8S1179"]
  },
  "interpretation": "Your sample is a confirmed match to authentic MCF-7. One locus shows a minor variation consistent with normal passage-related drift, not contamination.",
  "recommendation": "Safe to use. Consider returning to a lower-passage frozen stock for critical experiments.",
  "sources": ["clastr", "cellosaurus"]
}
```

**Error cases:**
- `400` — Malformed STR data (missing required loci, invalid allele format)
- `422` — Unable to determine a confident match (returns closest candidates with low confidence flag)

---

## POST `/api/cellcheck/methods-section`

**Purpose:** Generate a publication-ready methods paragraph.

**Request body:**
```json
{
  "cell_line": "MCF-7",
  "source": "ATCC HTB-22",
  "authentication_date": "2026-10-15",
  "authentication_service": "ATCC STR profiling",
  "mycoplasma_test_date": "2026-10-10",
  "passage_range": "8-15",
  "target_journal": "Cancer Research"
}
```

**Response (200 OK):**
```json
{
  "methods_paragraph": "The MCF-7 human breast adenocarcinoma cell line (RRID: CVCL_0031) was obtained from ATCC (Catalog: HTB-22). Cell line identity was authenticated by short tandem repeat (STR) profiling at ATCC on October 15, 2026...",
  "compliance_status": {
    "journal": "Cancer Research",
    "compliant": true,
    "missing_fields": []
  },
  "rrid_used": "CVCL_0031",
  "sources": ["cellosaurus", "journal_policy_reference"]
}
```

**Error cases:**
- `400` — Missing required fields
- `404` — Cell line not found (cannot generate accurate RRID citation)

---

## GET `/api/cellcheck/health`

**Purpose:** Health check for deployment verification.

**Response (200 OK):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "upstream_services": {
    "cellosaurus": "ok",
    "iclac": "ok",
    "semantic_scholar": "ok",
    "claude": "ok"
  }
}
```

---

## Standard Error Shape

All errors follow this shape:

```json
{
  "error": {
    "code": "CELL_LINE_NOT_FOUND",
    "message": "No cell line matching 'XYZ123' was found in Cellosaurus.",
    "details": null
  }
}
```

Common error codes:
- `CELL_LINE_NOT_FOUND`
- `INVALID_STR_FORMAT`
- `UPSTREAM_SERVICE_UNAVAILABLE`
- `MISSING_REQUIRED_FIELD`
- `LOW_CONFIDENCE_MATCH`

---

*End of document.*
