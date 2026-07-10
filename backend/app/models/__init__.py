# app/models/__init__.py
#
# CRITICAL: Import ALL models here so Alembic can detect their table definitions.
# SQLAlchemy only registers a table in Base.metadata when the model class is imported.
# If a model is not imported here → Alembic generates NO migration for it.
#
# RULE: Every new model file you add MUST be imported in this file.
#
# Milestone 2 — IAM
from app.models.user import User              # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401

# Future milestones (uncomment as models are built):
# from app.models.organization import Organization   # noqa: F401
# from app.models.membership import Membership       # noqa: F401
# from app.models.document import Document           # noqa: F401
# from app.models.document_chunk import DocumentChunk # noqa: F401
# from app.models.embedding import Embedding         # noqa: F401
# from app.models.chat import Chat                   # noqa: F401
# from app.models.message import Message             # noqa: F401
# from app.models.audit_log import AuditLog          # noqa: F401
