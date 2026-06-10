import unittest
import sys
import types
from unittest.mock import patch

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))
sys.modules.setdefault("groq", types.SimpleNamespace(Groq=object))
sys.modules.setdefault(
    "langchain_community.document_loaders",
    types.SimpleNamespace(PyPDFLoader=object),
)
sys.modules.setdefault(
    "langchain_text_splitters",
    types.SimpleNamespace(RecursiveCharacterTextSplitter=object),
)
sys.modules.setdefault("langchain_chroma", types.SimpleNamespace(Chroma=object))
sys.modules.setdefault(
    "langchain_community.embeddings",
    types.SimpleNamespace(HuggingFaceEmbeddings=object),
)

import rag_core


class FakeVectorDb:
    def __init__(self):
        self.called_with = None

    def similarity_search_with_score(self, question, k):
        self.called_with = (question, k)
        return [("doc-a", 0.42)]


class RetrieveDocsTests(unittest.TestCase):
    def test_retrieve_docs_returns_documents_with_scores(self):
        fake_db = FakeVectorDb()

        with patch("rag_core.load_vector_db", return_value=fake_db):
            results = rag_core.retrieve_docs("什么是闭环控制？", k=3)

        self.assertEqual(fake_db.called_with, ("什么是闭环控制？", 3))
        self.assertEqual(results, [("doc-a", 0.42)])

    def test_is_relevant_rejects_empty_or_high_distance_results(self):
        self.assertFalse(rag_core.has_relevant_docs([]))
        self.assertFalse(
            rag_core.has_relevant_docs([("doc-a", rag_core.MAX_RELEVANT_DISTANCE + 0.01)])
        )

    def test_is_relevant_accepts_distance_under_threshold(self):
        self.assertTrue(
            rag_core.has_relevant_docs([("doc-a", rag_core.MAX_RELEVANT_DISTANCE - 0.01)])
        )


if __name__ == "__main__":
    unittest.main()
