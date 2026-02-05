from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Request to create a new user."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str | None = Field(None, min_length=8)
    role: UserRole = UserRole.OPERATOR


class UserUpdate(BaseModel):
    """Request to update a user."""
    name: str | None = Field(None, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Response with user details."""
    id: str
    email: str
    name: str
    role: UserRole
    is_active: bool
    google_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInviteRequest(BaseModel):
    """Request to invite a user via email."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.OPERATOR


class UserInviteResponse(BaseModel):
    """Response from user invitation."""
    user_id: str
    email: str
    invite_url: str | None = None  # For email invitation link
    message: str


class UserListResponse(BaseModel):
    """Response with list of users."""
    items: list[UserResponse]
    total: int
    skip: int
    limit: int


class PasswordChangeRequest(BaseModel):
    """Request to change password."""
    current_password: str
    new_password: str = Field(..., min_length=8)
