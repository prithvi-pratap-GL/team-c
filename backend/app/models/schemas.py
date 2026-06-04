from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Department(str, Enum):
    engineering = "engineering"
    hr = "hr"
    operations = "operations"
    product_support = "product_support"


class Category(str, Enum):
    policy = "policy"
    guide = "guide"
    faq = "faq"
    incident = "incident"
    release_notes = "release_notes"


class ChunkingStrategy(str, Enum):
    fixed = "fixed"
    semantic = "semantic"


class RetrievalMode(str, Enum):
    vector = "vector"
    hybrid = "hybrid"


class Confidence(str, Enum):
    high = "high"
    low = "low"
    not_found = "not_found"


class Role(str, Enum):
    admin = "admin"
    engineering = "engineering"
    hr = "hr"
    operations = "operations"
    support = "support"


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    departments_allowed: List[Department]


class TokenUser(BaseModel):
    username: str
    role: Role
    departments_allowed: List[Department]


class IngestMetadata(BaseModel):
    department: Department
    category: Category
    version: str = Field(..., min_length=1)
    doc_date: str = Field(..., description="Date in ISO 8601 format (YYYY-MM-DD)")
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.fixed


class IngestResponse(BaseModel):
    job_id: str
    status: str = "processing"
    doc_id: str


class ChatFilters(BaseModel):
    department: Optional[Department] = None
    category: Optional[Category] = None
    year: Optional[int] = None
    doc_type: Optional[str] = None


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    filters: ChatFilters = Field(default_factory=ChatFilters)
    retrieval_mode: RetrievalMode = RetrievalMode.hybrid
    session_id: Optional[str] = None


class Source(BaseModel):
    doc_id: str
    doc_name: str
    department: Department
    chunk_text: str
    chunk_id: str
    score: float
    page: Optional[int] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    retrieval_mode_used: RetrievalMode
    confidence: Confidence
    session_id: str


class DocumentSummary(BaseModel):
    doc_id: str
    doc_name: str
    department: Department
    category: Category
    version: str
    doc_date: str
    chunk_count: int


class DocumentsResponse(BaseModel):
    documents: List[DocumentSummary]
    total: int
    page: int


class FeedbackRequest(BaseModel):
    session_id: str
    query: str
    helpful: bool
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str = "recorded"


class HealthResponse(BaseModel):
    message: str
    timestamp: datetime
