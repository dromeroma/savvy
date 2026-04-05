"""Organization context resolution middleware.

Sets ``request.state.org_id`` from the JWT claims (preferred) or from
the ``X-Org-ID`` header as a fallback for unauthenticated routes.
This middleware does **not** block requests -- org enforcement is
handled by dedicated FastAPI dependencies.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        org_id: uuid.UUID | None = None

        # Prefer org_id already placed in state by auth (e.g. get_current_user).
        if hasattr(request.state, "org_id") and request.state.org_id is not None:
            org_id = request.state.org_id

        # Fallback: read from explicit header.
        if org_id is None:
            header_value = request.headers.get("X-Org-ID")
            if header_value:
                try:
                    org_id = uuid.UUID(header_value)
                except ValueError:
                    pass

        request.state.org_id = org_id
        return await call_next(request)
