# app/middleware/__init__.py
# Middleware layer — cross-cutting concerns applied to every HTTP request.
# Middleware runs BEFORE route handlers and AFTER responses are generated.
#
# Current middleware:
#   - LoggingMiddleware   → request/response logging with request_id
#
# Future middleware (added in later milestones):
#   - RateLimitMiddleware → Redis-backed rate limiting per IP/user
