import os
import shutil

from dotenv import load_dotenv
from groq import Groq

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


PERSIST_DIR = "vector_db"

load_dotenv()


def load_pdf(file_path: str):
    """
    读取 PDF 文件，并过滤空白页面。
    """
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    documents = [
        doc for doc in documents
        if doc.page_content and doc.page_content.strip()
    ]

    return documents


def split_documents(documents):
    """
    把 PDF 文档切分成多个小文本块。
    """
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
        raise ValueError(
            "PDF 已读取，但切分后没有得到有效文本块。请换一个文字版 PDF 测试。"
        )

    return chunks


def get_embedding_model():
    """
    加载本地 Embedding 模型。
    第一次运行可能会下载模型。
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    return embeddings


def build_vector_db(chunks):
    """
    将文本块转换成向量，并保存到 Chroma 向量数据库。
    """
    if not chunks:
        raise ValueError("chunks 为空，无法建立向量数据库。")

    embeddings = get_embedding_model()

    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR
    )

    return vector_db


def load_vector_db():
    """
    加载已经建立好的 Chroma 向量数据库。
    """
    if not os.path.exists(PERSIST_DIR):
        raise ValueError("还没有建立知识库，请先上传 PDF 并点击“建立知识库”。")

    embeddings = get_embedding_model()

    vector_db = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )

    return vector_db


def build_knowledge_base(pdf_path: str):
    """
    从 PDF 文件一键建立知识库。

    流程：
    1. 读取 PDF
    2. 切分文本
    3. 本地 Embedding 向量化
    4. 存入 Chroma
    """
    documents = load_pdf(pdf_path)

    if not documents:
        raise ValueError(
            "没有从 PDF 中读取到有效文字。请使用文字版 PDF，不要使用扫描版 PDF。"
        )

    chunks = split_documents(documents)

    if not chunks:
        raise ValueError("文本切分失败，没有生成有效文本块。")

    build_vector_db(chunks)

    return len(documents), len(chunks)


def retrieve_docs(question: str, k: int = 4):
    """
    根据用户问题，从向量数据库中检索最相关的文本块。
    """
    if not question or not question.strip():
        raise ValueError("问题不能为空。")

    vector_db = load_vector_db()

    docs = vector_db.similarity_search(
        question,
        k=k
    )

    return docs


def generate_answer(question: str, docs):
    """
    调用 Groq API，根据检索到的参考片段生成中文回答。
    """
    if not question or not question.strip():
        raise ValueError("问题不能为空。")

    if not docs:
        raise ValueError("没有检索到参考资料，无法生成回答。")

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("没有找到 GROQ_API_KEY，请检查 .env 文件。")

    context = "\n\n".join(
        [
            f"参考片段 {i + 1}：\n{doc.page_content}"
            for i, doc in enumerate(docs)
        ]
    )

    client = Groq(
        api_key=api_key
    )

    prompt = f"""
你是一个自动化专业课程助教。

请严格根据下面的参考资料回答用户问题。
如果参考资料中没有相关信息，请回答：“知识库中没有找到相关内容”。

参考资料：
{context}

用户问题：
{question}

回答要求：
1. 用中文回答
2. 解释要适合自动化专业本科生理解
3. 不要编造参考资料中没有的信息
4. 如果涉及自动控制、PLC、传感器、电机等内容，请尽量结合自动化专业背景说明
5. 回答尽量条理清晰
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "你是一个严谨的自动化专业课程助教，只能根据给定资料回答。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


def clear_knowledge_base():
    """
    清空本地知识库。
    """
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)