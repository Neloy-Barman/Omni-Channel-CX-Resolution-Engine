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