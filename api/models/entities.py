"""Database entities using SQLModel."""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON


class User(SQLModel, table=True):
    """User entity for authentication and authorization."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str = Field(alias="password_hash")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    memberships: List["Membership"] = Relationship(back_populates="user")
    query_logs: List["QueryLog"] = Relationship(back_populates="user")


class Org(SQLModel, table=True):
    """Organization entity for multi-tenancy."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    plan: str = Field(default="basic")  # basic, pro, enterprise
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    memberships: List["Membership"] = Relationship(back_populates="org")
    docs: List["Doc"] = Relationship(back_populates="org")
    query_logs: List["QueryLog"] = Relationship(back_populates="org")
    rate_limits: List["RateLimit"] = Relationship(back_populates="org")


class Membership(SQLModel, table=True):
    """User membership in organizations with roles."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="org.id")
    user_id: int = Field(foreign_key="user.id")
    role: str = Field(default="member")  # owner, admin, member
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    org: Org = Relationship(back_populates="memberships")
    user: User = Relationship(back_populates="memberships")


class Doc(SQLModel, table=True):
    """Document entity for the policy corpus."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="org.id")
    source: str = Field(index=True)  # URL or file path
    uri: Optional[str] = None
    title: str = Field(index=True)
    text: str
    doc_metadata: str = Field(default="{}", sa_column=JSON)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    org: Org = Relationship(back_populates="docs")
    embeddings: List["Embedding"] = Relationship(back_populates="doc")


class Embedding(SQLModel, table=True):
    """Vector embeddings for document chunks."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    doc_id: int = Field(foreign_key="doc.id")
    chunk_text: str
    chunk_start: int  # Token position in document
    chunk_end: int
    vector: str = Field(sa_column=Vector(384))  # Dimension for all-MiniLM-L6-v2
    model: str = Field(default="text-embedding-3-small")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    doc: Doc = Relationship(back_populates="embeddings")


class QueryLog(SQLModel, table=True):
    """Log of all queries for analytics and monitoring."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="org.id")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    input_text: str
    tokens_in: int
    tokens_out: int
    vendor: str  # openai, anthropic, etc.
    cached: bool = Field(default=False)
    latency_ms: int
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    org: Org = Relationship(back_populates="query_logs")
    user: Optional[User] = Relationship(back_populates="query_logs")


class RateLimit(SQLModel, table=True):
    """Rate limiting configuration per organization."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="org.id", unique=True)
    rpm: int = Field(default=60)  # Requests per minute
    burst: int = Field(default=10)  # Burst capacity
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    org: Org = Relationship(back_populates="rate_limits")


class FeatureFlag(SQLModel, table=True):
    """Feature flags for controlling application behavior."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    enabled: bool = Field(default=False)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
