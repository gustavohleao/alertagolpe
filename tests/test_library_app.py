from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from estudapdf.demo import demo_pages
from estudapdf.document import split_pages
from estudapdf.retrieval import DocumentIndex


class LibraryAppTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=25).run()

    def test_switching_materials_keeps_progress_per_material(self):
        app = self.app()
        self.assertEqual(app.session_state["document_key"], "demo-v1")
        demo_history = app.session_state["tutor_history"]
        demo_history.append({"topic": "RAG", "evaluation": {"assessable": True, "score": 2}})

        pages = demo_pages()[:2]
        chunks = split_pages(pages)
        library = app.session_state["library"]
        # Nome hostil: deve aparecer só como texto escapado, nunca como Markdown/HTML.
        library["pdf:abc:aula.pdf"] = {"pages": pages, "chunks": chunks, "index": DocumentIndex(chunks), "history": [],
                                       "name": "![x](https://exemplo.invalid/pixel) aula.pdf", "kind": "Seu documento", "is_demo": False}
        app.run()
        open_buttons = [b for b in app.button if b.label == "Abrir"]
        self.assertEqual(len(open_buttons), 1)
        self.assertFalse(any("exemplo.invalid" in b.label for b in app.button))
        open_buttons[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["document_key"], "pdf:abc:aula.pdf")
        self.assertEqual(app.session_state["tutor_history"], [])

        next(b for b in app.button if b.label == "Abrir").click().run()
        self.assertEqual(app.session_state["document_key"], "demo-v1")
        self.assertEqual(len(app.session_state["tutor_history"]), 1)

    def test_removing_active_demo_without_other_material_shows_guidance(self):
        app = self.app()
        next(b for b in app.button if b.key and b.key.startswith("remove_")).click().run()
        self.assertFalse(app.exception)
        self.assertNotIn("demo-v1", app.session_state["library"])
        self.assertFalse(next(c for c in app.checkbox if c.label == "Usar material de demonstração").value)
        self.assertTrue(any("Carregue um PDF" in item.value for item in app.info))


if __name__ == "__main__":
    unittest.main()
