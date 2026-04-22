import os
import sys
import warnings

# 🔥 suppress all warnings globally
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 🔥 suppress stderr BEFORE imports (important)
sys.stderr = open(os.devnull, "w")


from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

try:
    import streamlit as st
    _cache = st.cache_resource
except Exception:
    # Fallback for non-Streamlit contexts (e.g. main.py CLI)
    def _cache(fn):
        from functools import lru_cache
        return lru_cache(maxsize=1)(fn)


@_cache
def _load_embedder():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


@_cache
def _load_db():
    embedder = _load_embedder()
    return FAISS.load_local(
        "rag/autostream_index",
        embedder,
        allow_dangerous_deserialization=True
    )


def get_retriever():
    return _load_db().as_retriever(search_kwargs={"k": 3})


def retrieve_context(query: str) -> str:
    retriever = get_retriever()

    try:
        docs = retriever.invoke(query)
    except Exception:
        return "No relevant information found."

    if not docs:
        return "No relevant information found."

    return "\n\n".join([doc.page_content for doc in docs])