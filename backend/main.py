from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .rag_core import (
    DATA_DIR,
    PERSIST_DIR,
    REFUSAL_MESSAGE,
    build_knowledge_base,
    clear_knowledge_base,
    generate_answer,
    generate_learning_content,
    has_relevant_docs,
    retrieve_docs,
)


ModelProvider = Literal["Groq", "DeepSeek"]
knowledge_base_lock = Lock()

app = FastAPI(
    title="AutoCourse-RAG API",
    version="1.0.0",
    description="面向自动化课程资料的 RAG 问答与学习辅助后端。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    model_provider: ModelProvider = "Groq"
    top_k: int = Field(default=4, ge=1, le=8)


class StudyRequest(BaseModel):
    model_provider: ModelProvider = "Groq"


class SourceItem(BaseModel):
    source: str
    page: int | str
    score: float
    content: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    is_refused: bool


class UploadResponse(BaseModel):
    page_count: int
    chunk_count: int
    files: list[str]


class StudyResponse(BaseModel):
    content: str


def get_knowledge_base_status():
    ready = PERSIST_DIR.exists() and any(PERSIST_DIR.iterdir())
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pdf_count = sum(1 for path in DATA_DIR.iterdir() if path.suffix.lower() == ".pdf")
    return ready, pdf_count


def sanitize_pdf_filename(filename: str | None):
    safe_name = Path(filename or "").name
    if not safe_name or Path(safe_name).suffix.lower() != ".pdf":
        raise ValueError("只支持上传 PDF 文件。")
    return safe_name


def rebuild_knowledge_base(upload_files: list[UploadFile]):
    if not upload_files:
        raise ValueError("请至少上传一个 PDF 文件。")

    filenames = [sanitize_pdf_filename(upload.filename) for upload in upload_files]

    with knowledge_base_lock:
        clear_knowledge_base()
        saved_paths = []

        for upload, filename in zip(upload_files, filenames):
            target_path = DATA_DIR / filename
            upload.file.seek(0)
            target_path.write_bytes(upload.file.read())
            saved_paths.append(target_path)

        page_count, chunk_count = build_knowledge_base(saved_paths)

    return page_count, chunk_count, filenames


def serialize_sources(docs):
    sources = []

    for doc, score in docs:
        metadata = getattr(doc, "metadata", {}) or {}
        source = Path(str(metadata.get("source", "未知来源"))).name
        page = metadata.get("page", "未知页码")
        if isinstance(page, int):
            page += 1

        sources.append(
            SourceItem(
                source=source,
                page=page,
                score=float(score),
                content=doc.page_content,
            )
        )

    return sources


def run_study_task(task_type: str, request: StudyRequest):
    try:
        content = generate_learning_content(
            task_type,
            provider=request.model_provider,
        )
        return StudyResponse(content=content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="学习辅助内容生成失败。") from exc


@app.get("/health")
def health():
    ready, pdf_count = get_knowledge_base_status()
    return {
        "status": "ok",
        "knowledge_base_ready": ready,
        "pdf_count": pdf_count,
    }


@app.post("/upload", response_model=UploadResponse)
def upload(files: list[UploadFile] = File(...)):
    try:
        page_count, chunk_count, filenames = rebuild_knowledge_base(files)
        return UploadResponse(
            page_count=page_count,
            chunk_count=chunk_count,
            files=filenames,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="知识库构建失败。") from exc


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        with knowledge_base_lock:
            docs = retrieve_docs(request.question, k=request.top_k)

        sources = serialize_sources(docs)
        if not has_relevant_docs(docs):
            return AskResponse(
                answer=REFUSAL_MESSAGE,
                sources=sources,
                is_refused=True,
            )

        answer = generate_answer(
            request.question,
            docs,
            provider=request.model_provider,
        )
        return AskResponse(
            answer=answer,
            sources=sources,
            is_refused=False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="问答生成失败。") from exc


@app.post("/study/summary", response_model=StudyResponse)
def study_summary(request: StudyRequest):
    return run_study_task("summary", request)


@app.post("/study/knowledge-points", response_model=StudyResponse)
def study_knowledge_points(request: StudyRequest):
    return run_study_task("knowledge_points", request)


@app.post("/study/quiz", response_model=StudyResponse)
def study_quiz(request: StudyRequest):
    return run_study_task("review_questions", request)


@app.post("/reset")
def reset():
    try:
        with knowledge_base_lock:
            clear_knowledge_base()
        return {"message": "知识库已清空。"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="知识库清空失败。") from exc
