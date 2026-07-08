# app/schemas/__init__.py
# Pydantic DTOs (Data Transfer Objects) for request validation and response serialization.
#
# RULE: Never expose SQLAlchemy ORM models directly from API responses.
#       Always serialize through a Pydantic schema.
#
# WHY? ORM models may expose sensitive fields (password_hash).
#       Schemas let you control exactly what the client sees.
