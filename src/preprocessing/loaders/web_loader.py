"""
DocumentLoader for OMS Maroc (and similar) web pages.

Fetches each URL with `requests`, extracts the main textual content with
BeautifulSoup, and returns one RawDocument per page. Extraction only — no
cleaning (TextCleaner) or chunking (TextChunker), per the DocumentLoader
contract.
"""
import random
import re
import time
from typing import Any, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from src.core.logging_config import get_logger
from src.preprocessing.interfaces.document_loader_interface import DocumentLoader, RawDocument

logger = get_logger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (compatible; M2IAD-MedicalRAG-Bot/1.0; "
    "projet universitaire UCD El Jadida)"
)
_REQUEST_TIMEOUT_SECONDS = 10
_MIN_DELAY_BETWEEN_REQUESTS_SECONDS = 1.0
_MAX_DELAY_BETWEEN_REQUESTS_SECONDS = 2.0
_TAGS_TO_STRIP = ("nav", "header", "footer", "script", "style")
_CONTENT_ID_OR_CLASS_PATTERN = re.compile("content", re.IGNORECASE)


def _slugify_url(url: str) -> str:
    parsed = urlparse(url)
    raw = f"{parsed.netloc}{parsed.path}"
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", raw).strip("-").lower()
    return slug or "page"


class OMSMarocWebLoader(DocumentLoader):
    """Loads each URL in `urls` into one `RawDocument` each.

    Args:
        urls: Pages to scrape (e.g. OMS Maroc guidance pages).
        institution: Stored in metadata["institution"] for all documents
            loaded by this instance (e.g. "OMS Maroc").
        language: Stored in metadata["language"].
    """

    def __init__(
        self,
        urls: list[str],
        institution: str = "OMS Maroc",
        language: str = "fr",
    ) -> None:
        self.urls = urls
        self.institution = institution
        self.language = language

    def load(self) -> List[RawDocument]:
        documents: List[RawDocument] = []
        last_index = len(self.urls) - 1
        for index, url in enumerate(self.urls):
            try:
                documents.append(self._load_one(url))
            except Exception as exc:
                logger.warning("Skipping unreachable page %s: %s", url, exc)
            if index < last_index:
                time.sleep(random.uniform(_MIN_DELAY_BETWEEN_REQUESTS_SECONDS, _MAX_DELAY_BETWEEN_REQUESTS_SECONDS))
        return documents

    def _load_one(self, url: str) -> RawDocument:
        response = requests.get(url, headers={"User-Agent": _USER_AGENT}, timeout=_REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag and title_tag.get_text(strip=True) else url

        for tag_name in _TAGS_TO_STRIP:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        main_content = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", id=_CONTENT_ID_OR_CLASS_PATTERN)
            or soup.find("div", class_=_CONTENT_ID_OR_CLASS_PATTERN)
            or soup.body
        )
        content = main_content.get_text(separator="\n", strip=True) if main_content else ""

        metadata: dict[str, Any] = {
            "institution": self.institution,
            "language": self.language,
        }

        return RawDocument(
            source_id=_slugify_url(url),
            title=title,
            content=content,
            source_url=url,
            metadata=metadata,
        )
