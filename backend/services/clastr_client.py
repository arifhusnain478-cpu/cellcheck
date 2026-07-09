"""Client for CLASTR STR similarity search (Cellosaurus / Expasy).

CLASTR: https://www.cellosaurus.org/str-search/
"""
from typing import Optional

import httpx

CLASTR_BASE_URL = "https://www.cellosaurus.org/str-search"


class ClastrClient:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client or httpx.AsyncClient(base_url=CLASTR_BASE_URL, timeout=60)

    async def search(self, str_profile: dict):
        # TODO: POST STR loci (e.g. {"Amelogenin": "X,Y", "D5S818": "11,12"})
        # and return ranked matches with similarity scores.
        raise NotImplementedError

    async def aclose(self) -> None:
        await self._client.aclose()
