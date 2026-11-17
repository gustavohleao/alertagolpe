"""Testes de validação de PDFs e preservação do contexto das páginas."""

from io import BytesIO
import unittest

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from estudapdf.document import DocumentError, Page, extract_pdf, split_pages


def pdf_bytes(page_texts: list[str | None], password: str | None = None) -> bytes:
    """PDF mínimo em memória para verificar extração, sem artefato no disco."""
    writer = PdfWriter()
    for text in page_texts:
        page = writer.add_blank_page(width=500, height=700)
        if text is not None:
            font = DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Font"),
                    NameObject("/Subtype"): NameObject("/Type1"),
                    NameObject("/BaseFont"): NameObject("/Helvetica"),
                }
            )
            page[NameObject("/Resources")] = DictionaryObject(
                {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
            )
            stream = DecodedStreamObject()
            safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream.set_data(f"BT /F1 12 Tf 30 650 Td ({safe_text}) Tj ET".encode("ascii"))
            page[NameObject("/Contents")] = writer._add_object(stream)
    if password:
        writer.encrypt(password)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


class DocumentTests(unittest.TestCase):
    def test_rejects_non_pdf_empty_and_corrupt_data(self):
        for data in (b"", b"nao e PDF", b"%PDF-1.7\nquebrado"):
            with self.subTest(data=data), self.assertRaises(DocumentError):
                extract_pdf(data)

    def test_rejects_scanned_or_empty_pages_with_ocr_guidance(self):
        with self.assertRaisesRegex(DocumentError, "OCR"):
            extract_pdf(pdf_bytes([None]))

    def test_rejects_password_protected_pdf(self):
        with self.assertRaisesRegex(DocumentError, "senha"):
            extract_pdf(pdf_bytes(["privado"], password="senha-de-teste"))

    def test_extraction_preserves_number_after_blank_page(self):
        pages = extract_pdf(pdf_bytes([None, "Redes neurais aprendem padroes."]))
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].number, 2)
        self.assertIn("Redes neurais", pages[0].text)

    def test_rejects_more_than_150_pages(self):
        with self.assertRaisesRegex(DocumentError, "150"):
            extract_pdf(pdf_bytes([None] * 151))

    def test_split_preserves_page_and_location_label(self):
        chunks = split_pages([Page(4, "  Aprendizado\n supervisionado. ", "Seção"), Page(8, " ")])
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].id, "P4-T1")
        self.assertEqual(chunks[0].page, 4)
        self.assertEqual(chunks[0].location_label, "Seção")
        self.assertEqual(chunks[0].text, "Aprendizado supervisionado.")

    def test_chunks_cover_all_characters_and_overlap_without_infinite_loop(self):
        text = "abcdefghijklmnopqrstuvwxyz" * 3
        chunks = split_pages([Page(1, text)], chunk_size=20, overlap=5)
        reconstructed = chunks[0].text + "".join(chunk.text[5:] for chunk in chunks[1:])
        self.assertEqual(reconstructed, text)
        self.assertTrue(all(len(chunk.text) <= 20 for chunk in chunks))
        self.assertEqual(len({chunk.id for chunk in chunks}), len(chunks))

    def test_extreme_overlap_still_advances(self):
        chunks = split_pages([Page(1, "abcdefghij")], chunk_size=3, overlap=2)
        self.assertEqual(chunks[-1].text, "hij")
        self.assertEqual(len(chunks), 8)

    def test_invalid_chunk_settings(self):
        for size, overlap in ((0, 0), (10, 10), (10, -1), (1.5, 0), (True, 0)):
            with self.subTest(size=size, overlap=overlap), self.assertRaises(ValueError):
                split_pages([Page(1, "texto")], size, overlap)


if __name__ == "__main__":
    unittest.main()

