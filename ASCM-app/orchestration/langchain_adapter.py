"""Minimal LangChain adapter stub showing how to connect a vectorstore + Supabase metadata.

This is a lightweight example for orchestration and decision support. It is intentionally small and
uses FAISS locally for the demo. Replace with a managed vector DB in production.
"""

from typing import List

try:
    from langchain import OpenAI
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import FAISS
    LCHAIN_AVAILABLE = True
except Exception:
    LCHAIN_AVAILABLE = False


def demo_chain(query: str) -> str:
    if not LCHAIN_AVAILABLE:
        return "LangChain not installed — install langchain and openai to enable this demo."
    # This is a placeholder: in production you would load a FAISS index and run a chain.
    return f"Received query: {query} — (demo response)"
