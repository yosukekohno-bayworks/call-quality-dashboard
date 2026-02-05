import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.api.deps import AdminUser, CurrentUser, get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    PasswordChangeRequest,
    UserCreate,
    UserInviteRequest,
    UserInviteResponse,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services.auth import get_password_hash, verify_password

router = APIRouter()


def user_to_response(user: User) -> UserResponse:
    """Convert User model to response."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        google_id=user.google_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: UserRole | None = None,
    is_active: bool | None = None,
    search: str | None = None,
):
    """
    List all users in the tenant.

    Admin only.
    """
    query = select(User).where(User.tenant_id == current_user.tenant_id)

    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_pattern)) | (User.name.ilike(search_pattern))
        )

    # Get total count
    count_query = select(func.count(User.id)).where(
        User.tenant_id == current_user.tenant_id
    )
    if role:
        count_query = count_query.where(User.role == role)
    if is_active is not None:
        count_query = count_query.where(User.is_active == is_active)
    if search:
        count_query = count_query.where(
            (User.email.ilike(search_pattern)) | (User.name.ilike(search_pattern))
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        items=[user_to_response(u) for u in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=UserResponse)
async def create_user(
    request: UserCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a new user in the tenant.

    Admin only.
    """
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        tenant_id=current_user.tenant_id,
        email=request.email,
        name=request.name,
        password_hash=get_password_hash(request.password) if request.password else None,
        role=request.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user_to_response(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: CurrentUser):
    """Get current user's profile."""
    return user_to_response(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str | None = None,
):
    """Update current user's profile."""
    if name is not None:
        current_user.name = name

    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)

    return user_to_response(current_user)


@router.post("/me/password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Change current user's password."""
    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for OAuth users",
        )

    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.password_hash = get_password_hash(request.new_password)
    current_user.updated_at = datetime.utcnow()
    await db.commit()

    return {"message": "Password changed successfully"}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get a specific user.

    Admin only.
    """
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user_to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    request: UserUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Update a user.

    Admin only.
    """
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent demoting the last admin
    if request.role and request.role != UserRole.ADMIN and user.role == UserRole.ADMIN:
        admin_count = await db.execute(
            select(func.count(User.id)).where(
                User.tenant_id == current_user.tenant_id,
                User.role == UserRole.ADMIN,
                User.is_active == True,
            )
        )
        if admin_count.scalar_one() <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last admin",
            )

    if request.name is not None:
        user.name = request.name
    if request.role is not None:
        user.role = request.role
    if request.is_active is not None:
        # Prevent deactivating self
        if user.id == current_user.id and not request.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself",
            )
        user.is_active = request.is_active

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    return user_to_response(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Delete a user.

    Admin only. Cannot delete yourself.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent deleting the last admin
    if user.role == UserRole.ADMIN:
        admin_count = await db.execute(
            select(func.count(User.id)).where(
                User.tenant_id == current_user.tenant_id,
                User.role == UserRole.ADMIN,
                User.is_active == True,
            )
        )
        if admin_count.scalar_one() <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin",
            )

    await db.delete(user)
    await db.commit()

    return {"message": "User deleted"}


@router.post("/invite", response_model=UserInviteResponse)
async def invite_user(
    request: UserInviteRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Invite a new user to the tenant.

    Creates a user account without password.
    User will need to set password via reset or use OAuth.
    """
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        tenant_id=current_user.tenant_id,
        email=request.email,
        name=request.name,
        role=request.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # TODO: Send invitation email with password setup link

    return UserInviteResponse(
        user_id=str(user.id),
        email=user.email,
        message="User invited. They can login using Google OAuth or request a password reset.",
    )


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    new_password: str,
):
    """
    Reset a user's password.

    Admin only.
    """
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.password_hash = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    await db.commit()

    return {"message": "Password reset successfully"}
