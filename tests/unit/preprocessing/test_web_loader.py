"""Unit tests for OMSMarocWebLoader.

`requests.get` is mocked throughout (no `requests-mock`/`responses` installed
in this project) so these tests never hit the network.
"""
from unittest.mock import patch

import pytest
import requests

from src.preprocessing.interfaces.document_loader_interface import DocumentLoader, RawDocument
from src.preprocessing.loaders.web_loader import OMSMarocWebLoader


class _FakeResponse:
    def __init__(self, text: str = "", status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code} Client Error")


@pytest.fixture(autouse=True)
def no_real_delay(monkeypatch: pytest.MonkeyPatch):
    """The loader sleeps 1-2s between requests; skip that in tests."""
    monkeypatch.setattr("src.preprocessing.loaders.web_loader.time.sleep", lambda _seconds: None)


def test_load_single_valid_page():
    html = """
    <html>
      <head><title>Guide de vaccination</title></head>
      <body>
        <nav>Accueil | Contact</nav>
        <article>La vaccination protege contre les maladies infectieuses.</article>
        <footer>Copyright OMS</footer>
      </body>
    </html>
    """
    url = "https://www.emro.who.int/fr/guide-vaccination"

    with patch("src.preprocessing.loaders.web_loader.requests.get", return_value=_FakeResponse(html)) as mock_get:
        loader = OMSMarocWebLoader(urls=[url], institution="OMS Maroc", language="fr")
        assert isinstance(loader, DocumentLoader)
        documents = loader.load()

    mock_get.assert_called_once()
    called_url, called_kwargs = mock_get.call_args[0][0], mock_get.call_args[1]
    assert called_url == url
    assert "M2IAD-MedicalRAG-Bot" in called_kwargs["headers"]["User-Agent"]
    assert called_kwargs["timeout"] == 10

    assert len(documents) == 1
    doc = documents[0]
    assert isinstance(doc, RawDocument)
    assert doc.title == "Guide de vaccination"
    assert "vaccination protege" in doc.content
    assert "Accueil" not in doc.content
    assert "Copyright" not in doc.content
    assert doc.source_url == url
    assert doc.source_id == "www-emro-who-int-fr-guide-vaccination"
    assert doc.metadata == {"institution": "OMS Maroc", "language": "fr"}


def test_load_skips_unreachable_urls_mixed_with_valid(caplog: pytest.LogCaptureFixture):
    timeout_url = "https://www.emro.who.int/fr/page-timeout"
    not_found_url = "https://www.emro.who.int/fr/page-404"
    valid_url = "https://www.emro.who.int/fr/page-valide"
    valid_html = "<html><head><title>Page valide</title></head><body><main>Contenu utile</main></body></html>"

    def fake_get(url, **_kwargs):
        if url == timeout_url:
            raise requests.exceptions.Timeout("timed out")
        if url == not_found_url:
            return _FakeResponse("not found", status_code=404)
        return _FakeResponse(valid_html)

    import logging

    with patch("src.preprocessing.loaders.web_loader.requests.get", side_effect=fake_get):
        loader = OMSMarocWebLoader(urls=[timeout_url, not_found_url, valid_url])
        with caplog.at_level(logging.WARNING, logger="src.preprocessing.loaders.web_loader"):
            documents = loader.load()

    assert len(documents) == 1
    assert documents[0].source_url == valid_url
    assert any(timeout_url in record.message for record in caplog.records)
    assert any(not_found_url in record.message for record in caplog.records)


def test_load_page_without_title_falls_back_to_url():
    html = "<html><body><main>Contenu sans titre</main></body></html>"
    url = "https://www.emro.who.int/fr/sans-titre"

    with patch("src.preprocessing.loaders.web_loader.requests.get", return_value=_FakeResponse(html)):
        loader = OMSMarocWebLoader(urls=[url])
        documents = loader.load()

    assert len(documents) == 1
    assert documents[0].title == url
    assert "Contenu sans titre" in documents[0].content
