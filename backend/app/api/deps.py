from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

# ---------------------------------------------------------------------------
# Re-export get_db for convenience.
#
# Routes import dependencies from deps.py (not directly from db.session).
# This single import point makes it easy to swap implementations during testing.
#
# Usage in routes:
#   from app.api.deps import get_db
#   @router.get("/")
#   def route(db: Session = Depends(get_db)):
#       ...
# ---------------------------------------------------------------------------

__all__ = ["get_db"]

# ---------------------------------------------------------------------------
# Future dependencies added here in later milestones:
#
# def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
#     db: Session = Depends(get_db),
# ) -> User:
#     """Validate JWT and return the authenticated User object."""
#     ...
#
# def get_current_org(current_user: User = Depends(get_current_user)) -> Organization:
#     """Return the organization the current user belongs to."""
#     ...
#
# def require_role(minimum_role: str):
#     """Factory function that creates a role-checking dependency."""
#     ...
# ---------------------------------------------------------------------------
