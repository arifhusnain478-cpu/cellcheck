"""Client for the Cellosaurus API — cell line identity and RRID lookup.

Docs: https://api.cellosaurus.org/
"""
from typing import Optional

import httpx

CELLOSAURUS_BASE_URL = "https://api.cellosaurus.org"


class CellosaurusClient:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client or httpx.AsyncClient(base_url=CELLOSAURUS_BASE_URL, timeout=30)

    async def search(self, query: str):
        # TODO: GET /search/cell-line?q=<query> and parse identity + RRID.
        raise NotImplementedError

    async def get_by_accession(self, accession: str):
        # TODO: GET /cell-line/<accession> (e.g. CVCL_0030 for HeLa).
        raise NotImplementedError

    async def aclose(self) -> None:
        await self._client.aclose()
