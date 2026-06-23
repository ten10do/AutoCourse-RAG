import shutil
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

if __package__:
    from .llm_client import generate_llm_answer
else:
    from llm_client import generate_llm_answer


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

REFUSAL_MESSAGE = "知识库中没有找到与该问题相关的内容，请换一个与课程资料相关的问题。"
EMPTY_KNOWLEDGE_BASE_MESSAGE = "请先上传 PDF 并构建知识库。"

# Light 模式将余弦相似度转换为距离，数值越小表示越相关。
MAX_RELEVANT_DISTANCE = 0.88
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


@dataclass
class LightDocument:
    page_content: str
    metadata: dict


_documents = []
_vectorizer = None
_tfidf_matrix = None


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        content = text[start:end].strip()
        if content:
            chunks.append(content)
        if end == len(text):
            break
        start = end - overlap

    return chunks


def build_knowledge_base(pdf_paths):
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    global _documents, _vectorizer, _tfidf_matrix

    if isinstance(pdf_paths, (str, Path)):
        pdf_paths = [pdf_paths]
    else:
        pdf_paths = list(pdf_paths)

    if not pdf_paths:
        raise ValueError("请先上传 PDF 文件。")

    documents = []
    page_count = 0

    for pdf_path in pdf_paths:
        reader = PdfReader(str(pdf_path))
        source_name = Path(pdf_path).name

        for page_number, page in enumerate(reader.pages):
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue

            page_count += 1
            for content in split_text(page_text):
                documents.append(
                    LightDocument(
                        page_content=content,
                        metadata={"source": source_name, "page": page_number},
                    )
                )

    if not documents:
        raise ValueError(
            "PDF 没有读取到有效文字内容。请使用文字版 PDF，不要使用扫描版 PDF。"
        )

    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 4),
        max_features=15000,
        dtype=np.float32,
    )
    tfidf_matrix = vectorizer.fit_transform(
        [document.page_content for document in documents]
    )

    _documents = documents
    _vectorizer = vectorizer
    _tfidf_matrix = tfidf_matrix
    return page_count, len(documents)


def is_knowledge_base_ready():
    return bool(_documents) and _vectorizer is not None and _tfidf_matrix is not None


def retrieve_docs(question: str, k: int = 4):
    from sklearn.metrics.pairwise import cosine_similarity

    if not question or not question.strip():
        raise ValueError("问题不能为空。")
    if not is_knowledge_base_ready():
        raise ValueError(EMPTY_KNOWLEDGE_BASE_MESSAGE)

    query_vector = _vectorizer.transform([question.strip()])
    similarities = cosine_similarity(query_vector, _tfidf_matrix).ravel()
    result_count = min(k, len(_documents))
    ranked_indices = similarities.argsort()[::-1][:result_count]

    return [
        (_documents[index], float(1.0 - similarities[index]))
        for index in ranked_indices
    ]


def has_relevant_docs(scored_docs):
    if not scored_docs:
        return False
    return scored_docs[0][1] <= MAX_RELEVANT_DISTANCE


def get_representative_docs(k: int = 8):
    if not is_knowledge_base_ready():
        raise ValueError(EMPTY_KNOWLEDGE_BASE_MESSAGE)
    return [(document, 0.0) for document in _documents[:k]]


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
""",
    }

    if task_type not in prompts:
        raise ValueError("不支持的学习辅助功能。")
    return prompts[task_type]


def generate_learning_content(task_type: str, provider: str = "Groq"):
    docs = get_representative_docs()
    return generate_llm_answer(
        get_learning_task_prompt(task_type),
        docs,
        provider=provider,
    )


def generate_answer(question: str, docs, provider: str = "Groq"):
    if not question or not question.strip():
        raise ValueError("问题不能为空。")
    if not docs:
        raise ValueError("没有检索到参考资料，无法生成回答。")
    return generate_llm_answer(question, docs, provider=provider)


def clear_knowledge_base():
    global _documents, _vectorizer, _tfidf_matrix

    _documents = []
    _vectorizer = None
    _tfidf_matrix = None

    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
