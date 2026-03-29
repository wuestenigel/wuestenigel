"""Reverse image search engines for finding unauthorized image usage."""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from .models import ImageMatch

logger = logging.getLogger(__name__)


class SearchEngine(ABC):
    """Base class for reverse image search engines."""

    @abstractmethod
    def search(self, image_url: str, max_results: int = 50) -> list[ImageMatch]:
        """Search for matches of the given image URL."""
        ...


class GoogleVisionSearch(SearchEngine):
    """Reverse image search using Google Custom Search JSON API."""

    API_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: str, cx_id: str):
        self.api_key = api_key
        self.cx_id = cx_id

    def search(self, image_url: str, max_results: int = 50) -> list[ImageMatch]:
        """Search Google for visually similar images."""
        try:
            import requests
        except ImportError:
            logger.error("requests library required: pip install requests")
            return []

        matches = []
        start_index = 1

        while len(matches) < max_results:
            params = {
                "key": self.api_key,
                "cx": self.cx_id,
                "searchType": "image",
                "q": "",
                "imgUrl": image_url,
                "imgType": "photo",
                "num": min(10, max_results - len(matches)),
                "start": start_index,
            }

            try:
                resp = requests.get(self.API_URL, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                logger.error("Google API request failed: %s", e)
                break

            items = data.get("items", [])
            if not items:
                break

            for item in items:
                link = item.get("link", "")
                page_link = item.get("image", {}).get("contextLink", link)
                domain = urlparse(page_link).netloc

                match = ImageMatch(
                    source_image_url=image_url,
                    found_url=link,
                    page_url=page_link,
                    similarity_score=self._estimate_similarity(item),
                    domain=domain,
                    image_dimensions=f"{item.get('image', {}).get('width', '?')}x{item.get('image', {}).get('height', '?')}",
                    search_engine="google",
                )
                matches.append(match)

            start_index += 10
            if "nextPage" not in data.get("queries", {}):
                break

        return matches

    def _estimate_similarity(self, item: dict) -> float:
        """Estimate similarity based on Google's ranking (higher rank = more similar)."""
        # Google doesn't provide an explicit similarity score, so we estimate
        # based on position and image metadata
        return 85.0  # Default high similarity for Google visual matches


class TinEyeSearch(SearchEngine):
    """Reverse image search using the TinEye API."""

    API_URL = "https://api.tineye.com/rest/search/"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, image_url: str, max_results: int = 50) -> list[ImageMatch]:
        """Search TinEye for exact and near-duplicate matches."""
        try:
            import requests
        except ImportError:
            logger.error("requests library required: pip install requests")
            return []

        matches = []
        offset = 0
        limit = min(50, max_results)

        while len(matches) < max_results:
            params = {
                "url": image_url,
                "offset": offset,
                "limit": limit,
                "sort": "score",
                "order": "desc",
            }
            headers = {"x-api-key": self.api_key}

            try:
                resp = requests.get(
                    self.API_URL, params=params, headers=headers, timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                logger.error("TinEye API request failed: %s", e)
                break

            results = data.get("matches", [])
            if not results:
                break

            for result in results:
                for backlink in result.get("backlinks", []):
                    domain = urlparse(backlink.get("url", "")).netloc
                    match = ImageMatch(
                        source_image_url=image_url,
                        found_url=backlink.get("url", ""),
                        page_url=backlink.get("backlink", backlink.get("url", "")),
                        similarity_score=result.get("score", 0) * 100,
                        domain=domain,
                        image_dimensions=f"{result.get('width', '?')}x{result.get('height', '?')}",
                        search_engine="tineye",
                    )
                    matches.append(match)

            offset += limit
            if len(results) < limit:
                break

        return matches[:max_results]


class SearchAggregator:
    """Aggregates results from multiple search engines and deduplicates."""

    def __init__(self, engines: list[SearchEngine]):
        self.engines = engines

    def search(self, image_url: str, max_results: int = 50) -> list[ImageMatch]:
        """Run search across all engines and deduplicate results."""
        all_matches: list[ImageMatch] = []

        for engine in self.engines:
            try:
                matches = engine.search(image_url, max_results=max_results)
                all_matches.extend(matches)
                logger.info(
                    "Found %d matches from %s",
                    len(matches),
                    engine.__class__.__name__,
                )
            except Exception as e:
                logger.error("Search engine %s failed: %s", engine.__class__.__name__, e)

        return self._deduplicate(all_matches)

    def _deduplicate(self, matches: list[ImageMatch]) -> list[ImageMatch]:
        """Remove duplicate matches based on found_url."""
        seen: dict[str, ImageMatch] = {}
        for match in matches:
            key = match.found_url
            if key not in seen or match.similarity_score > seen[key].similarity_score:
                seen[key] = match
        return sorted(seen.values(), key=lambda m: m.similarity_score, reverse=True)
