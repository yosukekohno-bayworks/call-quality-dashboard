from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.user import User, UserRole
from app.schemas.auth import (
    AuthResponse,
    GoogleAuthRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    Token,
    UserResponse,
)
from app.services.auth import (
    authenticate_user,
    create_tenant,
    create_tokens,
    create_user,
    decode_token,
    get_or_create_tenant_for_google_user,
    get_user_by_email,
    get_user_by_google_id,
    verify_google_token,
)

router = APIRouter()


def user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        tenant_id=str(user.tenant_id),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Login with email and password."""
    user = await authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    tokens = create_tokens(str(user.id))
    return AuthResponse(
        user=user_to_response(user),
        tokens=tokens,
    )


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Register a new user."""
    existing_user = await get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create or get tenant
    if request.tenant_name:
        tenant = await create_tenant(db, request.tenant_name)
        role = UserRole.ADMIN  # First user in tenant is admin
    else:
        # For now, require tenant name for registration
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant name is required for registration",
        )

    user = await create_user(
        db,
        email=request.email,
        name=request.name,
        password=request.password,
        tenant_id=tenant.id,
        role=role,
    )

    tokens = create_tokens(str(user.id))
    return AuthResponse(
        user=user_to_response(user),
        tokens=tokens,
    )


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Authenticate with Google OAuth."""
    google_info = verify_google_token(request.credential)
    if not google_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    # Check if user exists by Google ID
    user = await get_user_by_google_id(db, google_info["google_id"])

    if not user:
        # Check if user exists by email
        user = await get_user_by_email(db, google_info["email"])

        if user:
            # Link Google ID to existing user
            user.google_id = google_info["google_id"]
            await db.commit()
            await db.refresh(user)
        else:
            # Create new user and tenant based on email domain
            tenant = await get_or_create_tenant_for_google_user(db, google_info["email"])

            # Check if this is the first user in the tenant
            from sqlmodel import select, func

            result = await db.execute(
                select(func.count(User.id)).where(User.tenant_id == tenant.id)
            )
            user_count = result.scalar_one()
            role = UserRole.ADMIN if user_count == 0 else UserRole.OPERATOR

            user = await create_user(
                db,
                email=google_info["email"],
                name=google_info["name"],
                google_id=google_info["google_id"],
                tenant_id=tenant.id,
                role=role,
            )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    tokens = create_tokens(str(user.id))
    return AuthResponse(
        user=user_to_response(user),
        tokens=tokens,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)

    if not payload or payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    from sqlmodel import select

    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return create_tokens(str(user.id))


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Logout (client should discard tokens)."""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Get current user info."""
    return user_to_response(current_user)
