import importlib
import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace
from unittest.mock import patch


sys.modules.setdefault("dotenv", SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class LightRagCoreTests(unittest.TestCase):
    def test_multi_pdf_retrieval_metadata_refusal_and_reset(self):
        module_spec = importlib.util.find_spec("backend.light_rag_core")
        self.assertIsNotNone(module_spec)
        if module_spec is None:
            return

        light_rag_core = importlib.import_module("backend.light_rag_core")
        pdf_pages = {
            "feedback.pdf": [
                "反馈控制通过检测输出、形成偏差并调整控制作用来减小误差。",
                "负反馈能够提高抗干扰能力，但设计不当可能导致振荡。",
            ],
            "stability.pdf": [
                "稳定性是控制系统的基本要求，闭环极点应位于左半平面。",
            ],
        }

        def fake_reader(path):
            pages = [FakePage(text) for text in pdf_pages[Path(path).name]]
            return SimpleNamespace(pages=pages)

        with TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            with patch.object(light_rag_core, "DATA_DIR", data_dir):
                with patch.object(light_rag_core, "PdfReader", side_effect=fake_reader):
                    page_count, chunk_count = light_rag_core.build_knowledge_base(
                        [Path("feedback.pdf"), Path("stability.pdf")]
                    )

                self.assertEqual(page_count, 3)
                self.assertEqual(chunk_count, 3)
                self.assertTrue(light_rag_core.is_knowledge_base_ready())

                results = light_rag_core.retrieve_docs("反馈控制为什么需要稳定性分析", k=3)
                self.assertEqual(len(results), 3)
                self.assertLess(results[0][1], 1.0)
                self.assertTrue(light_rag_core.has_relevant_docs(results))
                self.assertEqual(
                    {result[0].metadata["source"] for result in results},
                    {"feedback.pdf", "stability.pdf"},
                )
                self.assertTrue(
                    all("page" in result[0].metadata for result in results)
                )

                unrelated = light_rag_core.retrieve_docs("量子化学分子轨道", k=1)
                self.assertFalse(light_rag_core.has_relevant_docs(unrelated))

                data_dir.mkdir(parents=True, exist_ok=True)
                (data_dir / "feedback.pdf").write_bytes(b"temporary")
                light_rag_core.clear_knowledge_base()
                self.assertFalse(light_rag_core.is_knowledge_base_ready())
                self.assertTrue(data_dir.exists())
                self.assertEqual(list(data_dir.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
