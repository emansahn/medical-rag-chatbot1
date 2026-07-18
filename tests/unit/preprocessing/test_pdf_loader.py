"""Unit tests for MinsanteDocPDFLoader.

reportlab is not in requirements/person1-data.txt (only pypdf, bs4, requests,
tiktoken), so test PDFs are hand-built as minimal valid PDF byte strings
instead of relying on an extra dependency.
"""
import logging
from pathlib import Path

import pytest

from src.preprocessing.interfaces.document_loader_interface import DocumentLoader, RawDocument
from src.preprocessing.loaders.pdf_loader import MinsanteDocPDFLoader


def _write_pdf(path: Path, text: str, title: str | None = None) -> None:
    """Write a minimal one-page, single-font PDF containing `text`, readable
    by pypdf's `extract_text()`, without pulling in reportlab."""
    content = f"BT /F1 24 Tf 100 700 Td ({text}) Tj ET".encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> "
        b"/MediaBox [0 0 300 144] /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    info_obj_num = None
    if title is not None:
        objects.append(f"<< /Title ({title}) >>".encode("latin-1"))
        info_obj_num = len(objects)

    body = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(body))
        body += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_offset = len(body)
    object_count = len(objects) + 1
    xref = f"xref\n0 {object_count}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        xref += f"{offset:010d} 00000 n \n".encode()

    info_entry = f" /Info {info_obj_num} 0 R" if info_obj_num else ""
    trailer = (
        f"trailer\n<< /Size {object_count} /Root 1 0 R{info_entry} >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    ).encode()

    path.write_bytes(bytes(body) + xref + trailer)


def test_load_single_valid_pdf(tmp_path: Path):
    _write_pdf(tmp_path / "guide-diabete.pdf", "Le diabete se previent par une alimentation equilibree.", title="Guide du diabete")

    loader = MinsanteDocPDFLoader(source_dir=tmp_path, institution="Ministere de la Sante", language="fr")
    assert isinstance(loader, DocumentLoader)

    documents = loader.load()

    assert len(documents) == 1
    doc = documents[0]
    assert isinstance(doc, RawDocument)
    assert doc.source_id == "guide-diabete"
    assert doc.title == "Guide du diabete"
    assert "diabete se previent" in doc.content
    assert doc.source_url == str(tmp_path / "guide-diabete.pdf")
    assert doc.metadata == {"institution": "Ministere de la Sante", "language": "fr", "num_pages": 1}


def test_load_empty_directory_returns_empty_list(tmp_path: Path):
    loader = MinsanteDocPDFLoader(source_dir=tmp_path)
    assert loader.load() == []


def test_load_multiple_pdfs_returns_alphabetical_order(tmp_path: Path):
    _write_pdf(tmp_path / "c_vaccination.pdf", "Contenu vaccination")
    _write_pdf(tmp_path / "a_diabete.pdf", "Contenu diabete")
    _write_pdf(tmp_path / "b_hypertension.pdf", "Contenu hypertension")

    loader = MinsanteDocPDFLoader(source_dir=tmp_path)
    documents = loader.load()

    assert [doc.source_id for doc in documents] == ["a_diabete", "b_hypertension", "c_vaccination"]


def test_load_skips_corrupted_pdf_and_logs_warning(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    _write_pdf(tmp_path / "valid.pdf", "Contenu valide")
    (tmp_path / "corrupt.pdf").write_bytes(b"this is not a real pdf file")

    loader = MinsanteDocPDFLoader(source_dir=tmp_path)

    with caplog.at_level(logging.WARNING, logger="src.preprocessing.loaders.pdf_loader"):
        documents = loader.load()

    assert [doc.source_id for doc in documents] == ["valid"]
    assert any("corrupt.pdf" in record.message for record in caplog.records)
