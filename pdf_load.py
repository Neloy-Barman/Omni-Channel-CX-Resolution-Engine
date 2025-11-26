from langchain_pymupdf4llm import PyMuPDF4LLMLoader

data_path = "data.pdf"

loader = PyMuPDF4LLMLoader(
    file_path=data_path
)

docs = loader.load()

# print(len(docs))

# print(docs[0])

from langchain_text_splitters import RecursiveCharacterTextSplitter, Language



splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.MARKDOWN,
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.split_documents(docs)

print(f"Chunks: {chunks[10].page_content}")
print(f"\nChunks: {chunks[11].page_content}")


from langchain_huggingface import HuggingFaceEmbeddings

model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {"device": "cpu"}
encode_kwargs = {"normalize_embeddings": True}
hf = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs,
    cache_folder="hf_storage"
)

text = "Hello, how are you"

response = hf.embed_query(
    text=text
)

print(f"Embedding Response: {response}")

print(len(response))

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

client = QdrantClient(
    # url="http://localhost:6333/"
    location="str",
    https=True,
    host="localhost",
    port=6333
)

collection_name = "Omni-Channel-CX-RAG-DB"

if client.collection_exists(collection_name=collection_name):
    client.delete_collection(collection_name=collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(
        size=768,
        distance=Distance.COSINE
    )
)

from langchain_qdrant import QdrantVectorStore

vector_store = QdrantVectorStore(
    client=client,
    collection_name=collection_name,
    embedding=hf
)

vector_store.add_documents(
    documents=chunks
)
print("Vector Store Created Successfully.")

query = "What is SRS"

results = vector_store.similarity_search(
    query=query,
    k=3
)

print(f"Results: {results}")

from qdrant_client import QdrantClient



