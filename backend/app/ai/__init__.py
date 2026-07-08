# app/ai/__init__.py
# AI / ML pipeline components.
#
# This module is the boundary between the business logic and AI infrastructure.
# All ML-related code (embedding, chunking, parsing, retrieval, LLM) lives here.
#
# WHY isolated? Swapping from SentenceTransformers to OpenAI embeddings
# only requires changes inside this folder — zero changes to services.
