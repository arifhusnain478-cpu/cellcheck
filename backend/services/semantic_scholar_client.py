"""Client for the Semantic Scholar API — find retracted / related papers.

Docs: https://api.semanticscholar.org/api-docs/graph
"""
from typing import Optional

import httpx

SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"


class SemanticScholarClient:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client or httpx.AsyncClient(base_url=SEMANTIC_SCHOLAR_BASE_URL, timeout=30)

    async def search_papers(self, query: str):
        # TODO: GET /paper/search?query=<query>&fields=title,externalIds,publicationTypes
        # and flag entries whose publicationTypes include "Retraction".
        raise NotImplementedError

    async def aclose(self) -> None:
        await self._client.aclose()
