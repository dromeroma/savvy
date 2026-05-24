"""Auth business logic: registration, login, token management, profile."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.exceptions import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from src.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
    verify_token,
)
from src.modules.auth.models import RefreshToken, User
from src.modules.church_hierarchy.models import (
    ChurchDenomination,
    ChurchZone,
    ChurchZoneLeader,
)
from src.modules.platform.models import PlatformRole, UserPlatformRole
from src.modules.auth.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    OrganizationResponse,
    OrgWithRole,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserUpdate,
)
from src.modules.organization.models import BusinessTypeCatalog, Membership, Organization

settings = get_settings()


async def _get_platform_role_codes(
    db: AsyncSession, user_id: uuid.UUID,
) -> list[str]:
    """Fetch the list of platform role codes granted to a user."""
    result = await db.execute(
        select(PlatformRole.code)
        .join(UserPlatformRole, UserPlatformRole.platform_role_id == PlatformRole.id)
        .where(
            UserPlatformRole.user_id == user_id,
            PlatformRole.is_active.is_(True),
        )
    )
    return [row[0] for row in result.all()]


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
        """Create organization, owner user, membership, and initial tokens.

        Wizard-driven fields (business_type, denomination, zone, zone_leader)
        are honored when present. The vertical's default app is auto-activated.
        """
        # Check slug uniqueness
        existing_org = await db.scalar(
            select(Organization).where(Organization.slug == data.slug),
        )
        if existing_org is not None:
            raise ConflictError("An organization with this slug already exists.")

        # Check email uniqueness (global)
        existing_user = await db.scalar(
            select(User).where(User.email == data.email),
        )
        if existing_user is not None:
            raise ConflictError("A user with this email already exists.")

        # Resolve and validate the business type / denomination / zone selection
        # before we mutate the DB so we fail fast on bad input.
        business_type_row = await self._resolve_business_type(db, data.business_type)
        if data.business_type is not None and data.business_type != "church" and (
            data.denomination_id or data.denomination_name or data.zone_id or data.claim_zone_leader
        ):
            raise ValidationError(
                "Denomination, zone and zone-leader fields only apply to business_type='church'.",
            )
        if data.business_type == "church":
            if data.denomination_id and data.denomination_name:
                raise ValidationError(
                    "Provide either denomination_id (existing) or denomination_name (custom), not both.",
                )

        # Create organization
        org = Organization(
            name=data.org_name,
            slug=data.slug,
            type="business",
            business_type=data.business_type,
        )
        db.add(org)
        await db.flush()  # need org.id for FK-bound rows below

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

        # Apply church-specific wiring (denomination, zone, zone leader)
        if data.business_type == "church":
            await self._apply_church_signup(db, org, user, data)

        # Auto-activate the vertical's default app (if any).
        if business_type_row is not None and business_type_row.default_app_code:
            # Imported here to avoid circular import at module load.
            from src.modules.apps.service import AppsService

            try:
                await AppsService.activate_app(
                    db, org.id, business_type_row.default_app_code, user.id,
                )
            except ConflictError:
                # Already active (shouldn't happen for a brand-new org, but defensive).
                pass

        # New accounts never have platform roles yet.
        token_data = {
            "sub": str(user.id),
            "org_id": str(org.id),
            "role": "owner",
            "platform_roles": [],
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
        await db.refresh(org)

        return AuthResponse(
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token_str,
            ),
            user=UserResponse.model_validate(user),
            organization=OrganizationResponse.model_validate(org),
        )

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------
    async def _resolve_business_type(
        self,
        db: AsyncSession,
        code: str | None,
    ) -> BusinessTypeCatalog | None:
        if not code:
            return None
        bt = await db.scalar(
            select(BusinessTypeCatalog).where(
                BusinessTypeCatalog.code == code,
                BusinessTypeCatalog.is_active.is_(True),
            )
        )
        if bt is None:
            raise ValidationError(f"Unknown business_type: '{code}'.")
        return bt

    async def _apply_church_signup(
        self,
        db: AsyncSession,
        org: Organization,
        user: User,
        data: RegisterRequest,
    ) -> None:
        """Attach denomination, zone and (optionally) zone-leader to a church org."""
        denomination_id: uuid.UUID | None = None

        if data.denomination_id is not None:
            denom = await db.scalar(
                select(ChurchDenomination).where(
                    ChurchDenomination.id == data.denomination_id,
                    # Either system or owned by this org (org won't own anything yet
                    # in a fresh signup, but kept for symmetry with later edits).
                    (ChurchDenomination.created_by_org_id.is_(None))
                    | (ChurchDenomination.created_by_org_id == org.id),
                )
            )
            if denom is None:
                raise NotFoundError("Denomination not found or not accessible.")
            denomination_id = denom.id
        elif data.denomination_name is not None:
            # Create a custom denomination owned by the new org.
            custom_code = (
                data.denomination_name.lower().replace(" ", "-")[:50] or "custom"
            )
            denom = ChurchDenomination(
                code=custom_code,
                name=data.denomination_name,
                is_system=False,
                created_by_org_id=org.id,
            )
            db.add(denom)
            await db.flush()
            denomination_id = denom.id

        org.denomination_id = denomination_id

        if data.zone_id is not None:
            if denomination_id is None:
                raise ValidationError(
                    "zone_id requires a denomination (denomination_id or denomination_name).",
                )
            zone = await db.scalar(
                select(ChurchZone).where(
                    ChurchZone.id == data.zone_id,
                    ChurchZone.denomination_id == denomination_id,
                )
            )
            if zone is None:
                raise NotFoundError("Zone not found for the selected denomination.")
            org.zone_id = zone.id

            if data.claim_zone_leader:
                leader = ChurchZoneLeader(
                    user_id=user.id,
                    zone_id=zone.id,
                    organization_id=org.id,
                    role="presbitero",
                )
                db.add(leader)

        await db.flush()

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    async def login(
        self,
        db: AsyncSession,
        data: LoginRequest,
    ) -> LoginResponse:
        """Authenticate user by email and password.

        If the user belongs to 1 org → returns tokens directly.
        If 2+ orgs and no org_id provided → returns org list for selection.
        If 2+ orgs and org_id provided → returns tokens for that org.
        """
        # Find user by email
        user = await db.scalar(
            select(User).where(User.email == data.email),
        )
        if user is None or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Invalid credentials.")

        if user.deleted_at is not None:
            raise UnauthorizedError("This account has been deactivated.")

        # Get all memberships
        result = await db.execute(
            select(Membership, Organization)
            .join(Organization, Organization.id == Membership.organization_id)
            .where(Membership.user_id == user.id)
            .order_by(Membership.joined_at),
        )
        memberships = result.all()

        if not memberships:
            raise UnauthorizedError("No organization found for this user.")

        # Always attach platform roles to the returned user so the
        # frontend can redirect super admins to /platform right after login.
        platform_roles = await _get_platform_role_codes(db, user.id)
        user_response = UserResponse.model_validate(user)
        user_response.platform_roles = platform_roles

        # Multiple orgs and no org_id specified → return list
        if len(memberships) > 1 and data.org_id is None:
            orgs_with_roles = [
                OrgWithRole(
                    id=org.id,
                    name=org.name,
                    slug=org.slug,
                    type=org.type,
                    role=mem.role,
                )
                for mem, org in memberships
            ]
            return LoginResponse(
                user=user_response,
                organizations=orgs_with_roles,
                requires_org_selection=True,
            )

        # Resolve which org to use
        if data.org_id:
            # Find the specific membership
            match = next(
                ((mem, org) for mem, org in memberships if org.id == data.org_id),
                None,
            )
            if match is None:
                raise UnauthorizedError("You are not a member of this organization.")
            membership, org = match
        else:
            # Single org → use it directly
            membership, org = memberships[0]

        # Update last login
        user.last_login_at = datetime.now(UTC)
        await db.flush()

        # Platform roles already fetched above — reuse
        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "org_id": str(org.id),
            "role": membership.role,
            "platform_roles": platform_roles,
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

        return LoginResponse(
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token_str,
            ),
            user=user_response,
            organization=OrganizationResponse.model_validate(org),
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

        # Re-fetch platform roles (may have changed since last token)
        platform_roles = await _get_platform_role_codes(
            db, uuid.UUID(payload["sub"]),
        )

        # Issue new pair with same family_id
        token_data = {
            "sub": payload["sub"],
            "org_id": payload["org_id"],
            "role": payload.get("role", "member"),
            "platform_roles": platform_roles,
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

    async def get_current_user_response(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> UserResponse:
        """Fetch the user profile enriched with platform_roles."""
        user = await self.get_current_user_profile(db, user_id)
        roles = await _get_platform_role_codes(db, user_id)
        response = UserResponse.model_validate(user)
        response.platform_roles = roles
        return response

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
