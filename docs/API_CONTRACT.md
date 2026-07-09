# API Contract

The canonical API contract lives in the **[PRD](PRD.md)** (see the *API Contract* section at the
bottom). That document is the single source of truth — do not duplicate endpoint shapes here.

## Quick reference

Base URL (local dev): `http://localhost:8000`

| Method | Path | Mode |
| --- | --- | --- |
| `GET` | `/api/cellcheck/health` | Health check |
| `POST` | `/api/cellcheck/quick` | Quick Check |
| `POST` | `/api/cellcheck/str-analysis` | STR Test Reader |
| `POST` | `/api/cellcheck/methods-section` | Methods Section Generator |

See [PRD.md](PRD.md) for full request/response bodies, error cases, and the standard error shape.
