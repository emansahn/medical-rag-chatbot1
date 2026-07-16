"""
Authentication placeholder.

No real auth is required for this academic deliverable, but the seam is
here so adding real authentication later (JWT, OAuth...) means editing this
ONE file, not every router. Every router that will eventually need auth
already depends on `get_current_user`, not on nothing.
"""
from dataclasses import dataclass

from fastapi import Header


@dataclass
class CurrentUser:
    """Represents the authenticated caller. Anonymous today."""

    user_id: str
    is_anonymous: bool = True


def get_current_user(x_user_id: str | None = Header(default=None)) -> CurrentUser:
    """Placeholder dependency.

    TODO(future work): validate a real JWT/session token here and raise
    `AuthenticationError` (add to `src/core/exceptions.py`) on failure.
    Today it just accepts an optional `X-User-Id` header for local testing,
    defaulting to a fixed anonymous identity.
    """
    if x_user_id:
        return CurrentUser(user_id=x_user_id, is_anonymous=False)
    return CurrentUser(user_id="anonymous", is_anonymous=True)
