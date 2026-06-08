from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DepartmentEnum(str, Enum):
    engineering = "engineering"
    hr = "hr"
    operations = "operations"
    product_support = "product_support"


# Keep Department as alias for backwards compatibility in the rest of the code
Department = DepartmentEnum


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
    medium = "medium"
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
    departments_allowed: List[str]


class TokenUser(BaseModel):
    username: str
    role: Role
    departments_allowed: List[str]


class UserProfile(BaseModel):
    id: int
    username: str
    role: Role
    departments_allowed: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class IngestMetadata(BaseModel):
    department: Department
    category: Category
    version: str = Field(..., min_length=1)
    doc_date: date
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


# ── Chat Session schemas ─────────────────────────────────────────────

class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    meta_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionChatRequest(BaseModel):
    """Used for POST /chat/sessions/{id}/messages"""
    query: str = Field(..., min_length=1)
    filters: ChatFilters = Field(default_factory=ChatFilters)
    retrieval_mode: RetrievalMode = RetrievalMode.hybrid


class SuggestionsResponse(BaseModel):
    suggestions: List[str]


# ── Documents / Feedback / Health (unchanged) ────────────────────────

class DocumentSummary(BaseModel):
    doc_id: str
    doc_name: str
    department: Department
    category: Category
    version: str
    doc_date: date
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


# ── Admin Schemas ────────────────────────────────────────────────────

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = None


class DepartmentUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCreateAdmin(BaseModel):
    username: str = Field(..., min_length=2, max_length=80)
    email: Optional[str] = None
    password: str = Field(..., min_length=4)
    role: str
    departments_allowed: List[str]


class UserUpdateAdmin(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    departments_allowed: Optional[List[str]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserAdminResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    departments_allowed: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UsersListResponse(BaseModel):
    users: List[UserAdminResponse]
    total: int
    page: int
    page_size: int


class AdminDocumentResponse(BaseModel):
    id: int
    doc_id: str
    doc_name: str
    department: str
    category: str
    version: str
    doc_date: date
    file_type: str
    file_size: int
    chunk_count: int
    uploaded_by: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdminDocumentsListResponse(BaseModel):
    documents: List[AdminDocumentResponse]
    total: int
    page: int
    page_size: int


class OverviewStats(BaseModel):
    total_users: int
    total_documents: int
    total_departments: int
    total_chat_sessions: int
    total_questions_asked: int


class TopUser(BaseModel):
    username: str
    question_count: int


class TopQuestion(BaseModel):
    query: str
    count: int


class DeptDocCount(BaseModel):
    department: str
    count: int


class AnalyticsResponse(BaseModel):
    total_questions: int
    total_sessions: int
    top_users: List[TopUser]
    most_asked: List[TopQuestion]
    docs_by_department: List[DeptDocCount]


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    actor: str
    action: str
    target: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True


class AuditLogsListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
