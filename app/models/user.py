import uuid
from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    ADMIN = "admin"
    SV = "sv"  # Supervisor
    QA = "qa"  # Quality Assurance
    OPERATOR = "operator"
    EXECUTIVE = "executive"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: uuid.UUID = Field(foreign_key="tenants.id", index=True)
    email: str = Field(max_length=255, unique=True, index=True)
    password_hash: str | None = Field(default=None, max_length=255)
    google_id: str | None = Field(default=None, max_length=255, unique=True)
    role: UserRole = Field(default=UserRole.OPERATOR)
    name: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
