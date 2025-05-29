import os
from fastapi import FastAPI, HTTPException
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import pandas as pd
from typing import List, Dict
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Enhanced Retriever Agent")

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")
INDEX_NAME = os.getenv("PINECONE_INDEX", "finance-agent")
PORTFOLIO_PATH = "/app/portfolio.csv"  # Update path for container

# Initialize Pinecone with new client
pc = None
index = None

try:
    if PINECONE_API_KEY:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Check if index exists, create if not
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        
        if INDEX_NAME not in existing_indexes:
            pc.create_index(
                name=INDEX_NAME,
                dimension=384,  # For sentence-transformers/all-MiniLM-L6-v2
                metric="cosine",
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        
        index = pc.Index(INDEX_NAME)
    else:
        print("Warning: PINECONE_API_KEY not set, using mock mode")
except Exception as e:
    print(f"Warning: Could not initialize Pinecone: {e}")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Data models
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3
    filter_tickers: List[str] = None

class DocumentResult(BaseModel):
    id: str
    score: float
    content: str
    metadata: Dict

class PortfolioAnalysis(BaseModel):
    ticker: str
    current_value: float
    allocation_pct: float
    related_documents: List[DocumentResult]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "retriever-agent", "pinecone_connected": index is not None}

@app.on_event("startup")
async def startup_event():
    """Initialize portfolio data on startup"""
    # Create sample portfolio if file doesn't exist
    if not os.path.exists(PORTFOLIO_PATH):
        print(f"Portfolio file not found at {PORTFOLIO_PATH}, creating sample data")
        sample_data = {
            "ticker": ["AAPL", "GOOGL", "TSLA", "MSFT", "AMZN"],
            "quantity": [50, 30, 25, 60, 20],
            "price_per_stock": [180.0, 140.0, 200.0, 350.0, 150.0],
            "current_value": [9000.0, 4200.0, 5000.0, 21000.0, 3000.0]
        }
        df = pd.DataFrame(sample_data)
        df.to_csv(PORTFOLIO_PATH, index=False)

@app.post("/upsert")
async def upsert_documents(chunks: List[Dict]):
    """
    Upsert documents with metadata
    Format: [{"text": "...", "metadata": {"ticker": "AAPL", "date": "...", ...}}]
    """
    if not index:
        return {"upserted": 0, "error": "Pinecone not available"}
    
    try:
        texts = [item["text"] for item in chunks]
        embeddings = model.encode(texts).tolist()
        
        vectors = []
        for i, (item, emb) in enumerate(zip(chunks, embeddings)):
            vector_id = f"{item['metadata'].get('ticker', 'global')}_{datetime.now().timestamp()}_{i}"
            vectors.append({
                "id": vector_id,
                "values": emb,
                "metadata": {**item["metadata"], "text": item["text"]}
            })
        
        index.upsert(vectors=vectors)
        return {"upserted": len(vectors)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_documents(request: QueryRequest):
    """Enhanced query with filtering and metadata"""
    if not index:
        # Return mock data if Pinecone not available
        return {
            "results": [
                DocumentResult(
                    id="mock_1",
                    score=0.9,
                    content="Asia tech sector showing strong performance with TSMC reporting better than expected earnings.",
                    metadata={"ticker": "2330.TW", "date": "2024-01-15"}
                ),
                DocumentResult(
                    id="mock_2", 
                    score=0.8,
                    content="Samsung semiconductor division continues to face headwinds from memory chip oversupply.",
                    metadata={"ticker": "005930.KS", "date": "2024-01-14"}
                )
            ]
        }
    
    try:
        # Encode query
        vec = model.encode([request.query])[0].tolist()
        
        # Prepare filters
        filter_dict = None
        if request.filter_tickers:
            filter_dict = {"ticker": {"$in": request.filter_tickers}}
        
        # Query Pinecone
        res = index.query(
            vector=vec,
            top_k=request.top_k,
            include_metadata=True,
            filter=filter_dict
        )
        
        # Format results
        results = []
        for match in res.matches:
            results.append(DocumentResult(
                id=match.id,
                score=match.score,
                content=match.metadata.get("text", ""),
                metadata=match.metadata
            ))
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio-analysis")
async def analyze_portfolio():
    """Analyze portfolio with related documents"""
    try:
        # Load portfolio
        if not os.path.exists(PORTFOLIO_PATH):
            raise HTTPException(status_code=404, detail="Portfolio file not found")
            
        portfolio = pd.read_csv(PORTFOLIO_PATH)
        total_value = portfolio["current_value"].sum()
        
        results = []
        for _, row in portfolio.iterrows():
            # Get related documents for each ticker
            query = f"Latest financial performance and risk factors for {row['ticker']}"
            docs_result = await query_documents(QueryRequest(
                query=query,
                filter_tickers=[row["ticker"]],
                top_k=2
            ))
            
            results.append(PortfolioAnalysis(
                ticker=row["ticker"],
                current_value=row["current_value"],
                allocation_pct=(row["current_value"] / total_value) * 100,
                related_documents=docs_result["results"]
            ))
        
        return {"analysis": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)