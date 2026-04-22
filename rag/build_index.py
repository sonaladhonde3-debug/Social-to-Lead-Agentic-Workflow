from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter

def build_index():
    text = open("rag/knowledge_base.md").read()

    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("##", "section"), ("###", "subsection")]
    )

    docs = splitter.split_text(text)

    embedder = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.from_documents(docs, embedder)
    vectorstore.save_local("rag/autostream_index")

if __name__ == "__main__":
    build_index()