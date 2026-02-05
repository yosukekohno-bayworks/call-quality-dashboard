import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Operator(SQLModel, table=True):
    __tablename__ = "operators"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: uuid.UUID = Field(foreign_key="tenants.id", index=True)
    biztel_operator_id: str = Field(max_length=255, index=True)
    name: str = Field(max_length=255)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
