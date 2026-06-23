import os
import shutil
from pathlib import Path
from types import SimpleNamespace

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

if __package__:
    from .llm_client import generate_llm_answer
else:
    from llm_client import generate_llm_answer


BASE_DIR = Path(__file__).resolve().parent
PERSIST_DIR = BASE_DIR / "vector_db"
DATA_DIR = BASE_DIR / "data"

REFUSAL_MESSAGE = "知识库中没有找到与该问题相关的内容，请换一个与课程资料相关的问题。"
EMPTY_KNOWLEDGE_BASE_MESSAGE = "请先上传 PDF 并构建知识库。"

# Chroma 在当前 Embedding 配置下返回原始距离值，数值越小表示越相关。
MAX_RELEVANT_DISTANCE = 20.0


def load_pdf(file_path: str | os.PathLike):
    loader = PyPDFLoader(str(file_path))
    documents = loader.load()
    documents = [
        doc for doc in documents
        if doc.page_content and doc.page_content.strip()
    ]

    source_name = Path(file_path).name
    for page_number, doc in enumerate(documents):
        doc.metadata["source"] = source_name
        doc.metadata.setdefault("page", page_number)

    return documents


def split_documents(documents):
    if not documents:
        raise ValueError(
            "PDF 没有读取到有效文字内容。请使用文字版 PDF，不要使用扫描版 PDF。"
        )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )
    chunks = text_splitter.split_documents(documents)
    chunks = [
        chunk for chunk in chunks
        if chunk.page_content and chunk.page_content.strip()
    ]

    if not chunks:
        raise ValueError("PDF 切分后没有得到有效文本块。")

    return chunks


def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )


def build_vector_db(chunks):
    if not chunks:
        raise ValueError("chunks 为空，无法建立向量数据库。")

    return Chroma.from_documents(
        documents=chunks,
        embedding=get_embedding_model(),
        persist_directory=str(PERSIST_DIR)
    )


def load_vector_db():
    if not PERSIST_DIR.exists():
        raise ValueError(EMPTY_KNOWLEDGE_BASE_MESSAGE)

    return Chroma(
        persist_directory=str(PERSIST_DIR),
        embedding_function=get_embedding_model()
    )


def build_knowledge_base(pdf_paths):
    if isinstance(pdf_paths, (str, os.PathLike)):
        pdf_paths = [pdf_paths]
    else:
        pdf_paths = list(pdf_paths)

    if not pdf_paths:
        raise ValueError("请先上传 PDF 文件。")

    all_documents = []
    all_chunks = []

    for path in pdf_paths:
        documents = load_pdf(path)
        if not documents:
            raise ValueError(
                f"没有从 {Path(path).name} 中读取到有效文字。请使用文字版 PDF。"
            )

        chunks = split_documents(documents)
        all_documents.extend(documents)
        all_chunks.extend(chunks)

    clear_vector_db()
    build_vector_db(all_chunks)

    return len(all_documents), len(all_chunks)


def retrieve_docs(question: str, k: int = 4):
    if not question or not question.strip():
        raise ValueError("问题不能为空。")

    vector_db = load_vector_db()
    return vector_db.similarity_search_with_score(question, k=k)


def has_relevant_docs(scored_docs):
    if not scored_docs:
        return False

    return scored_docs[0][1] <= MAX_RELEVANT_DISTANCE


def get_representative_docs(k: int = 8):
    vector_db = load_vector_db()
    result = vector_db.get(
        include=["documents", "metadatas"],
        limit=k
    )

    documents = result.get("documents", [])
    metadatas = result.get("metadatas", [])
    representative_docs = []

    for index, content in enumerate(documents):
        if not content or not content.strip():
            continue

        metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
        doc = SimpleNamespace(page_content=content, metadata=metadata)
        representative_docs.append((doc, 0.0))

    return representative_docs


def get_learning_task_prompt(task_type: str):
    prompts = {
        "summary": """
请基于当前课程资料生成课程总结，必须包括：
1）课程资料主要内容
2）核心章节或主题
3）重点概念
4）学习建议
要求：只依据参考资料总结，不要脱离资料自由发挥。
""",
        "knowledge_points": """
请基于当前课程资料提取自动化课程相关核心知识点。
要求：每个知识点给出简短解释，并尽量按课程模块分类，不要脱离资料自由发挥。
""",
        "review_questions": """
请基于当前课程资料生成 5 道选择题、3 道判断题和 2 道简答题。
每道题必须给出参考答案，不要生成与资料无关的题目。
"""
    }

    if task_type not in prompts:
        raise ValueError("不支持的学习辅助功能。")

    return prompts[task_type]


def generate_learning_content(task_type: str, provider: str = "Groq"):
    docs = get_representative_docs()
    if not docs:
        raise ValueError(EMPTY_KNOWLEDGE_BASE_MESSAGE)

    return generate_llm_answer(
        get_learning_task_prompt(task_type),
        docs,
        provider=provider
    )


def generate_answer(question: str, docs, provider: str = "Groq"):
    if not question or not question.strip():
        raise ValueError("问题不能为空。")

    if not docs:
        raise ValueError("没有检索到参考资料，无法生成回答。")

    return generate_llm_answer(question, docs, provider=provider)


def clear_vector_db():
    if PERSIST_DIR.exists():
        shutil.rmtree(PERSIST_DIR)


def clear_data_dir():
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)

    DATA_DIR.mkdir(parents=True, exist_ok=True)


def clear_knowledge_base():
    clear_vector_db()
    clear_data_dir()
