# app/services/__init__.py
# Business logic layer.
#
# Services orchestrate use cases. They:
# - Call repositories for data access
# - Call the AI layer for embeddings / LLM
# - Apply business rules
# - Raise domain exceptions (NotFoundException, etc.)
#
# RULE: Services must NOT import FastAPI, Request, or Response.
#       They should be independently testable without an HTTP layer.
