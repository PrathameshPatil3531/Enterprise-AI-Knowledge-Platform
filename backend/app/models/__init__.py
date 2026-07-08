# app/models/__init__.py
#
# WHY this file is critical:
# Alembic's env.py imports Base.metadata to detect schema changes.
# SQLAlchemy only knows about a table if the model class has been imported.
# If a model is not imported here, Alembic will NOT generate a migration for it.
#
# RULE: Every new model file you create MUST be imported in this file.
#
# Example (uncomment as models are built in future milestones):
# from app.models.organization import Organization   # noqa: F401
# from app.models.user import User                   # noqa: F401
# from app.models.membership import Membership       # noqa: F401
# from app.models.document import Document           # noqa: F401
# from app.models.document_chunk import DocumentChunk # noqa: F401
# from app.models.embedding import Embedding         # noqa: F401
# from app.models.chat import Chat                   # noqa: F401
# from app.models.message import Message             # noqa: F401
# from app.models.refresh_token import RefreshToken  # noqa: F401
# from app.models.audit_log import AuditLog          # noqa: F401
