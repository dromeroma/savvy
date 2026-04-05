"""Auth business logic: registration, login, token management, profile."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from src.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
    verify_token,
)
from src.modules.auth.models import RefreshToken, User
from src.modules.auth.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    OrganizationResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserUpdate,
)
from src.modules.organization.models import Membership, Organization

settings = get_settings()


class AuthService:
    """Encapsulates all authentication and user-profile operations."""

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    async def register(
        self,
        db: AsyncSession,
        data: RegisterRequest,
    ) -> AuthResponse:
        """Create organization, owner user, membership, and initial tokens."""
        # Check slug uniqueness
        existing_org = await db.scalar(
            select(Organization).where(Organization.slug == data.slug),
        )
        if existing_org is not None:
            raise ConflictError("An organization with this slug already exists.")

        # Create organization
        org = Organization(
            name=data.org_name,
            slug=data.slug,
            type="business",
        )
        db.add(org)
        await db.flush()

        # Check email uniqueness (global)
        existing_user = await db.scalar(
            select(User).where(User.email == data.email),
        )
        if existing_user is not None:
            raise ConflictError("A user with this email already exists.")

        # Create user (no organization FK — users are global)
        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
        )
        db.add(user)
        await db.flush()

        # Create owner membership
        membership = Membership(
            organization_id=org.id,
            user_id=user.id,
            role="owner",
        )
        db.add(membership)
        await db.flush()

        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "org_id": str(org.id),
            "role": "owner",
        }
        access_token = create_access_token(token_data)
        refresh_token_str = create_refresh_token(token_data)

        # Store hashed refresh token with family_id
        family_id = uuid.uuid4()
        rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token_str),
            family_id=family_id,
            expires_at=datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(rt)
        await db.flush()

        return AuthResponse(
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token_str,
            ),
            user=UserResponse.model_validate(user),
            organization=OrganizationResponse.model_validate(org),
        )

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    async def login(
        self,
        db: AsyncSession,
        data: LoginRequest,
    ) -> TokenResponse:
        """Authenticate user by email, password, and organization slug."""
        # Find organization
        org = await db.scalar(
            select(Organization).where(Organization.slug == data.org_slug),
        )
        if org is None:
            raise UnauthorizedError("Invalid credentials.")

        # Find user by email (globally unique)
        user = await db.scalar(
            select(User).where(User.email == data.email),
        )
        if user is None or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Invalid credentials.")

        if user.deleted_at is not None:
            raise UnauthorizedError("This account has been deactivated.")

        # Verify user is a member of this organization
        membership = await db.scalar(
            select(Membership).where(
                and_(
                    Membership.organization_id == org.id,
                    Membership.user_id == user.id,
                ),
            ),
        )
        if membership is None:
            raise UnauthorizedError("Invalid credentials.")

        # Update last login
        user.last_login_at = datetime.now(UTC)
        await db.flush()

        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "org_id": str(org.id),
            "role": membership.role,
        }
        access_token = create_access_token(token_data)
        refresh_token_str = create_refresh_token(token_data)

        # Store hashed refresh token
        family_id = uuid.uuid4()
        rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token_str),
            family_id=family_id,
            expires_at=datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(rt)
        await db.flush()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
        )

    # ------------------------------------------------------------------
    # Refresh token (with rotation)
    # ------------------------------------------------------------------
    async def refresh_token(
        self,
        db: AsyncSession,
        token: str,
    ) -> TokenResponse:
        """Validate a refresh token, revoke it, and issue a new pair."""
        token_hashed = hash_token(token)

        # Look up the stored token by hash
        stored = await db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hashed),
        )
        if stored is None:
            raise UnauthorizedError("Invalid refresh token.")

        if stored.revoked_at is not None:
            # Token reuse detected — revoke entire family
            from sqlalchemy import update
            await db.execute(
                update(RefreshToken)
                .where(
                    and_(
                        RefreshToken.family_id == stored.family_id,
                        RefreshToken.revoked_at.is_(None),
                    )
                )
                .values(revoked_at=datetime.now(UTC))
            )
            await db.flush()
            raise UnauthorizedError("Refresh token has been revoked. All sessions in this family have been invalidated.")

        if stored.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            raise UnauthorizedError("Refresh token has expired.")

        # Verify the JWT signature
        try:
            payload = verify_token(token)
        except Exception:
            raise UnauthorizedError("Invalid refresh token.")

        # Revoke the old token
        stored.revoked_at = datetime.now(UTC)
        await db.flush()

        # Issue new pair with same family_id
        token_data = {
            "sub": payload["sub"],
            "org_id": payload["org_id"],
            "role": payload.get("role", "member"),
        }
        new_access = create_access_token(token_data)
        new_refresh = create_refresh_token(token_data)

        rt = RefreshToken(
            user_id=uuid.UUID(payload["sub"]),
            token_hash=hash_token(new_refresh),
            family_id=stored.family_id,
            expires_at=datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(rt)
        await db.flush()

        return TokenResponse(access_token=new_access, refresh_token=new_refresh)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------
    async def logout(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        token: str,
    ) -> None:
        """Revoke a specific refresh token owned by the user."""
        token_hashed = hash_token(token)
        stored = await db.scalar(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token_hash == token_hashed,
                    RefreshToken.user_id == user_id,
                ),
            ),
        )
        if stored is None:
            raise NotFoundError("Refresh token not found.")

        stored.revoked_at = datetime.now(UTC)
        await db.flush()

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------
    async def get_current_user_profile(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> User:
        """Fetch the authenticated user's profile."""
        user = await db.scalar(
            select(User).where(User.id == user_id),
        )
        if user is None:
            raise NotFoundError("User not found.")
        return user

    async def update_profile(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        data: UserUpdate,
    ) -> User:
        """Update the authenticated user's profile fields."""
        user = await self.get_current_user_profile(db, user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await db.flush()
        return user

    async def change_password(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        data: ChangePasswordRequest,
    ) -> None:
        """Change the authenticated user's password."""
        user = await self.get_current_user_profile(db, user_id)

        if not verify_password(data.current_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect.")

        user.password_hash = hash_password(data.new_password)
        await db.flush()


# Module-level singleton
auth_service = AuthService()
