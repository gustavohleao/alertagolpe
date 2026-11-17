"""Leitura local de PDFs e divisão de texto com localização da fonte."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import re

from pypdf import PdfReader


MAX_PDF_BYTES = 15 * 1024 * 1024
MAX_PDF_PAGES = 150
MAX_EXTRACTED_CHARS = 1_500_000
MAX_PAGE_STREAM_BYTES = 8 * 1024 * 1024


class DocumentError(ValueError):
    """Documento inválido ou não suportado pelo protótipo."""


@dataclass(frozen=True)
class Page:
    number: int
    text: str
    location_label: str = "Página"


@dataclass(frozen=True)
class Chunk:
    id: str
    page: int
    text: str
    location_label: str = "Página"


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\x00", "")).strip()


def extract_pdf(data: bytes) -> list[Page]:
    """Extrai texto por página; não envia o documento a serviços externos.

    Os limites são proteções práticas para documentos de sala de aula, não um
    isolamento de execução para PDFs hostis. Imagens não passam por OCR.
    """
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise DocumentError("O arquivo está vazio. Selecione um PDF com texto.")
    if len(data) > MAX_PDF_BYTES:
        raise DocumentError("O PDF excede o limite de 15 MB.")
    if not data[:1024].lstrip().startswith(b"%PDF-"):
        raise DocumentError("O arquivo não parece ser um PDF válido.")

    try:
        reader = PdfReader(BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise DocumentError(
                "O PDF está protegido por senha. Use uma cópia sem proteção "
                "que você tenha autorização para consultar."
            )
        page_count = len(reader.pages)
        if page_count > MAX_PDF_PAGES:
            raise DocumentError("O PDF excede o limite de 150 páginas.")
        if not page_count:
            raise DocumentError("O PDF não contém páginas.")

        pages: list[Page] = []
        extracted_chars = 0
        for number, page in enumerate(reader.pages, start=1):
            contents = page.get_contents()
            if contents is not None and len(contents.get_data()) > MAX_PAGE_STREAM_BYTES:
                raise DocumentError(
                    f"A página {number} tem conteúdo interno muito grande. "
                    "Use um PDF menor ou simplificado."
                )
            text = page.extract_text() or ""
            extracted_chars += len(text)
            if extracted_chars > MAX_EXTRACTED_CHARS:
                raise DocumentError(
                    "O PDF contém texto demais para este protótipo. "
                    "Use um documento menor."
                )
            normalized = _normalize_text(text)
            if normalized:
                pages.append(Page(number=number, text=normalized))
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError(
            "Não foi possível ler o PDF. O arquivo pode estar incompleto, "
            "danificado ou usar uma estrutura não suportada."
        ) from exc

    if not pages:
        raise DocumentError(
            "Não foi encontrado texto selecionável. Este protótipo não faz OCR; "
            "use um PDF textual em vez de páginas escaneadas."
        )
    return pages


def split_pages(
    pages: list[Page], chunk_size: int = 1100, overlap: int = 180
) -> list[Chunk]:
    """Divide cada página separadamente sem perder sua referência original.

    Trechos vizinhos repetem até ``overlap`` caracteres para reduzir a perda
    de contexto nas bordas. O limite é em caracteres, não em tokens do modelo.
    """
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("O tamanho do trecho deve ser um inteiro positivo.")
    if isinstance(overlap, bool) or not isinstance(overlap, int) or not 0 <= overlap < chunk_size:
        raise ValueError("A sobreposição deve ser um inteiro entre zero e o tamanho do trecho menos um.")

    chunks: list[Chunk] = []
    for page in pages:
        text = _normalize_text(page.text)
        start = 0
        index = 1
        while start < len(text):
            end = min(start + chunk_size, len(text))
            # Prefere o fim de uma palavra sem comprometer o avanço do laço.
            if end < len(text):
                boundary = text.rfind(" ", start + max(overlap + 1, chunk_size // 2), end)
                if boundary > start + overlap:
                    end = boundary
            value = text[start:end].strip()
            if value:
                chunks.append(
                    Chunk(
                        id=f"P{page.number}-T{index}",
                        page=page.number,
                        text=value,
                        location_label=page.location_label,
                    )
                )
                index += 1
            if end >= len(text):
                break
            start = end - overlap
    return chunks

