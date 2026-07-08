# app/repositories/__init__.py
# Data access layer (Repository Pattern).
#
# Repositories are the ONLY place in the codebase that write SQLAlchemy queries.
# Services call repositories — services never call db.query() directly.
#
# WHY? If you need to change how users are fetched (add a filter, change join),
#       you change ONE function in ONE file. Services are unaffected.
#
# WHY? Makes testing trivial — mock the repository, no real DB needed.
