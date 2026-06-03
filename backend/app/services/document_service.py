import re
import uuid
from datetime import date
from io import BytesIO
from typing import Iterable, List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import db_models
from app.models.schemas import Department, IngestMetadata, TokenUser


WORD_RE = re.compile(r"[a-zA-Z0-9_]+")


def tokenize(text: str) -> List[str]:
    return WORD_RE.findall(text.lower())


def extract_text(file: UploadFile, content: bytes) -> str:
    filename = (file.filename or "").lower()
    if filename.endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except Exception:
            return ""

    return content.decode("utf-8", errors="ignore")


def chunk_text(text: str) -> Iterable[tuple[str, int]]:
    settings = get_settings()
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    chunks = []
    start = 0
    text_length = len(normalized)
    step = max(settings.chunk_size - settings.chunk_overlap, 1)

    while start < text_length:
        end = min(start + settings.chunk_size, text_length)
        if end < text_length:
            sentence_end = normalized.rfind(".", start, end)
            if sentence_end > start + settings.chunk_size // 2:
                end = sentence_end + 1

        chunks.append((normalized[start:end].strip(), start))
        start += step

    return chunks


def create_document(
    db: Session,
    file: UploadFile,
    content: bytes,
    metadata: IngestMetadata,
    current_user: TokenUser,
) -> db_models.Document:
    doc_id = str(uuid.uuid4())
    text = extract_text(file, content)
    chunks = list(chunk_text(text))

    document = db_models.Document(
        doc_id=doc_id,
        doc_name=file.filename or "uploaded-document",
        department=metadata.department.value,
        category=metadata.category.value,
        version=metadata.version,
        doc_date=metadata.doc_date,
        chunking_strategy=metadata.chunking_strategy.value,
        file_type=(file.filename or "").split(".")[-1].lower() or "unknown",
        file_size=len(content),
        chunk_count=len(chunks),
        uploaded_by=current_user.username,
    )
    db.add(document)

    for index, (chunk, offset) in enumerate(chunks, start=1):
        db.add(
            db_models.Chunk(
                chunk_id=f"{doc_id}:{index}",
                doc_id=doc_id,
                chunk_text=chunk,
                char_offset=offset,
            )
        )

    db.commit()
    db.refresh(document)
    return document


def list_documents(
    db: Session,
    departments: List[Department],
    category: Optional[str],
    page: int,
    page_size: int,
) -> tuple[List[db_models.Document], int]:
    query = db.query(db_models.Document).filter(
        db_models.Document.department.in_([dept.value for dept in departments])
    )
    if category:
        query = query.filter(db_models.Document.category == category)

    total = query.count()
    documents = (
        query.order_by(db_models.Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return documents, total


def search_chunks(
    db: Session,
    query_text: str,
    departments: List[Department],
    category: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = 5,
) -> List[tuple[db_models.Chunk, float]]:
    query_terms = tokenize(query_text)
    if not query_terms:
        return []

    db_query = (
        db.query(db_models.Chunk)
        .join(db_models.Document)
        .filter(db_models.Document.department.in_([dept.value for dept in departments]))
    )
    if category:
        db_query = db_query.filter(db_models.Document.category == category)
    if year:
        db_query = db_query.filter(db_models.Document.doc_date >= date(year, 1, 1))
        db_query = db_query.filter(db_models.Document.doc_date <= date(year, 12, 31))

    scored = []
    query_set = set(query_terms)
    for chunk in db_query.all():
        chunk_terms = tokenize(chunk.chunk_text)
        chunk_set = set(chunk_terms)
        overlap = len(query_set & chunk_set)
        phrase_bonus = 2 if query_text.lower() in chunk.chunk_text.lower() else 0
        score = (overlap + phrase_bonus) / max(len(query_set), 1)
        if score > 0:
            scored.append((chunk, round(score, 4)))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]
