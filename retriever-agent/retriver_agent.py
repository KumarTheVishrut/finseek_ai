import os
from fastapi import FastAPI
import pinecone
from sentence_transformers import SentenceTransformer

app = FastAPI(title="Retriever Agent")

# Load Pinecone configuration from environment
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
PINECONE_HOST = os.getenv("PINECONE_HOST")  # e.g., https://finance-agent-xgjs5rq.svc.aped-4627-b74a.pinecone.io
INDEX_NAME = os.getenv("PINECONE_INDEX", "finance-agent")

# Initialize Pinecone
pinecone.init(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENV,
    host=PINECONE_HOST
)
index = pinecone.Index(INDEX_NAME)

# Load embedding model
# llama-text-embed-v2 outputs 1024-d vectors
model = SentenceTransformer("llama-text-embed-v2")

@app.post("/upsert")
async def upsert(chunks: list[str]):
    # Embed and upsert
    embeddings = model.encode(chunks).tolist()
    vectors = [(str(i), emb) for i, emb in enumerate(embeddings)]
    index.upsert(vectors=vectors)
    return {"upserted": len(vectors)}

@app.get("/query")
async def query(q: str, top_k: int = 3):
    # Encode query
    vec = model.encode([q])[0].tolist()
    # Query Pinecone with cosine metric
    res = index.query(
        vector=vec,
        top_k=top_k,
        include_data=False
    )
    return {"matches": [{"id": m.id, "score": m.score} for m in res.matches]}
