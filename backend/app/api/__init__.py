# app/api/__init__.py
# HTTP API layer — route handlers only.
#
# RULE: Route handlers must be thin controllers.
#   ✅ Validate input (Pydantic does this automatically)
#   ✅ Call a service method
#   ✅ Return a response schema
#   ❌ NO business logic
#   ❌ NO database queries
#   ❌ NO AI calls
#
# All routes are versioned under app/api/v1/ from day one.
