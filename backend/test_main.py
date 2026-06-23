import importlib
import os
from pathlib import Path
import unittest
import sys
import types
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))
sys.modules.setdefault("langchain_chroma", types.SimpleNamespace(Chroma=object))
sys.modules.setdefault(
    "langchain_community.document_loaders",
    types.SimpleNamespace(PyPDFLoader=object),
)
sys.modules.setdefault(
    "langchain_community.embeddings",
    types.SimpleNamespace(HuggingFaceEmbeddings=object),
)
sys.modules.setdefault(
    "langchain_text_splitters",
    types.SimpleNamespace(RecursiveCharacterTextSplitter=object),
)

from backend.main import app
import backend.main as main_module


class FastApiBackendTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_returns_service_status(self):
        with patch("backend.main.get_knowledge_base_status", return_value=(True, 2)):
            response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "knowledge_base_ready": True,
                "pdf_count": 2,
            },
        )

    def test_upload_accepts_multiple_pdf_files_and_builds_knowledge_base(self):
        files = [
            ("files", ("course-a.pdf", b"pdf-a", "application/pdf")),
            ("files", ("course-b.pdf", b"pdf-b", "application/pdf")),
        ]

        with patch(
            "backend.main.rebuild_knowledge_base",
            return_value=(8, 24, ["course-a.pdf", "course-b.pdf"]),
        ) as rebuild:
            response = self.client.post("/upload", files=files)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["page_count"], 8)
        self.assertEqual(response.json()["chunk_count"], 24)
        self.assertEqual(response.json()["files"], ["course-a.pdf", "course-b.pdf"])
        self.assertEqual(len(rebuild.call_args.args[0]), 2)

    def test_ask_returns_answer_and_serialized_sources(self):
        docs = [
            (
                SimpleNamespace(
                    page_content="PLC 扫描周期参考内容",
                    metadata={"source": "course.pdf", "page": 0},
                ),
                9.25,
            )
        ]

        with patch("backend.main.retrieve_docs", return_value=docs):
            with patch("backend.main.has_relevant_docs", return_value=True):
                with patch("backend.main.generate_answer", return_value="模型回答") as generate:
                    response = self.client.post(
                        "/ask",
                        json={
                            "question": "PLC 的扫描周期是什么？",
                            "model_provider": "DeepSeek",
                        },
                    )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["answer"], "模型回答")
        self.assertFalse(payload["is_refused"])
        self.assertEqual(
            payload["sources"],
            [
                {
                    "source": "course.pdf",
                    "page": 1,
                    "score": 9.25,
                    "content": "PLC 扫描周期参考内容",
                }
            ],
        )
        generate.assert_called_once_with(
            "PLC 的扫描周期是什么？",
            docs,
            provider="DeepSeek",
        )

    def test_ask_refuses_irrelevant_question_without_calling_model(self):
        docs = [(SimpleNamespace(page_content="无关片段", metadata={}), 40.0)]

        with patch("backend.main.retrieve_docs", return_value=docs):
            with patch("backend.main.has_relevant_docs", return_value=False):
                with patch("backend.main.generate_answer") as generate:
                    response = self.client.post(
                        "/ask",
                        json={"question": "今天天气如何？", "model_provider": "Groq"},
                    )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_refused"])
        generate.assert_not_called()

    def test_study_endpoints_use_expected_task_types(self):
        cases = [
            ("/study/summary", "summary"),
            ("/study/knowledge-points", "knowledge_points"),
            ("/study/quiz", "review_questions"),
        ]

        for path, task_type in cases:
            with self.subTest(path=path):
                with patch(
                    "backend.main.generate_learning_content",
                    return_value="学习辅助结果",
                ) as generate:
                    response = self.client.post(
                        path,
                        json={"model_provider": "DeepSeek"},
                    )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["content"], "学习辅助结果")
                generate.assert_called_once_with(task_type, provider="DeepSeek")

    def test_reset_clears_backend_knowledge_base(self):
        with patch("backend.main.clear_knowledge_base") as clear:
            response = self.client.post("/reset")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "知识库已清空。")
        clear.assert_called_once_with()

    def test_cors_allows_localhost_and_loopback_frontend_origins(self):
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            with self.subTest(origin=origin):
                response = self.client.options(
                    "/health",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "GET",
                    },
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.headers["access-control-allow-origin"],
                    origin,
                )

    def test_cors_allows_frontend_origin_from_environment(self):
        frontend_origin = "https://autocourse-rag.example.com"

        with patch.dict(os.environ, {"FRONTEND_ORIGIN": frontend_origin}):
            deployed_module = importlib.reload(main_module)
            deployed_client = TestClient(deployed_module.app)
            response = deployed_client.options(
                "/health",
                headers={
                    "Origin": frontend_origin,
                    "Access-Control-Request-Method": "GET",
                },
            )

        importlib.reload(main_module)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            frontend_origin,
        )

    def test_render_root_directory_can_import_main_app(self):
        backend_dir = Path(__file__).resolve().parent
        import_error = None
        sys.path.insert(0, str(backend_dir))

        try:
            for module_name in ("main", "rag_core", "llm_client"):
                sys.modules.pop(module_name, None)
            render_main = importlib.import_module("main")
        except Exception as exc:
            import_error = exc
            render_main = None
        finally:
            sys.path.remove(str(backend_dir))
            for module_name in ("main", "rag_core", "llm_client"):
                sys.modules.pop(module_name, None)

        self.assertIsNone(import_error)
        self.assertIsNotNone(getattr(render_main, "app", None))


if __name__ == "__main__":
    unittest.main()
