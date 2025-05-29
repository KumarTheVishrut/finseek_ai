from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import httpx
import asyncio
from typing import List, Dict, Optional
import logging
import pandas as pd
from datetime import datetime

app = FastAPI(title="Finance Agent Orchestrator")

# Service URLs for Kubernetes
API_AGENT_URL = "http://api-agent-service:8000"
SCRAPER_AGENT_URL = "http://scraper-agent-service:8001"
RETRIEVER_AGENT_URL = "http://retriever-agent-service:8002"
LANG_AGENT_URL = "http://lang-agent-service:8003"

# Request models
class MarketBriefRequest(BaseModel):
    query: str
    portfolio_focus: Optional[str] = None
    region: Optional[str] = "asia"

class VoiceRequest(BaseModel):
    query: str
    return_audio: bool = True

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/voice-query")
async def handle_voice_query(audio: UploadFile = File(...)):
    """Handle voice input and return voice/text response"""
    try:
        # Step 1: Convert speech to text
        async with httpx.AsyncClient() as client:
            files = {"audio": (audio.filename, await audio.read(), audio.content_type)}
            stt_response = await client.post(f"{LANG_AGENT_URL}/stt", files=files)
            stt_response.raise_for_status()
            transcript = stt_response.json()["transcript"]
            
        logger.info(f"Transcript: {transcript}")
        
        # Step 2: Process the query
        brief_response = await generate_market_brief(MarketBriefRequest(query=transcript))
        
        # Step 3: Convert response to speech
        async with httpx.AsyncClient() as client:
            tts_response = await client.post(
                f"{LANG_AGENT_URL}/tts", 
                json={"text": brief_response["response"]}
            )
            tts_response.raise_for_status()
            audio_file = tts_response.json()["audio_file"]
        
        return {
            "transcript": transcript,
            "response": brief_response["response"],
            "audio_file": audio_file,
            "market_data": brief_response.get("market_data", {}),
            "portfolio_analysis": brief_response.get("portfolio_analysis", {})
        }
        
    except Exception as e:
        logger.error(f"Voice query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/market-brief")
async def generate_market_brief(request: MarketBriefRequest):
    """Generate comprehensive market brief with portfolio analysis"""
    try:
        # Parallel data gathering
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = []
            
            # Task 1: Get portfolio analysis
            tasks.append(client.get(f"{RETRIEVER_AGENT_URL}/portfolio-analysis"))
            
            # Task 2: Get market data for Asia tech stocks
            asia_tech_tickers = ["2330.TW", "005930.KS", "9988.HK", "ASML"]  # TSMC, Samsung, Alibaba, ASML
            tasks.append(client.get(
                f"{API_AGENT_URL}/risk-exposure",
                params={"ticker_list": ",".join(asia_tech_tickers)}
            ))
            
            # Task 3: Get earnings surprises
            tasks.append(client.get(f"{SCRAPER_AGENT_URL}/earnings-surprises?symbol=2330"))
            
            # Task 4: Query relevant documents
            tasks.append(client.post(
                f"{RETRIEVER_AGENT_URL}/query",
                json={
                    "query": f"Asia tech stocks market outlook earnings {request.query}",
                    "top_k": 5,
                    "filter_tickers": asia_tech_tickers
                }
            ))
            
            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        # Process results
        portfolio_data = results[0].json() if not isinstance(results[0], Exception) else {}
        market_data = results[1].json() if not isinstance(results[1], Exception) else {}
        earnings_data = results[2].json() if not isinstance(results[2], Exception) else {}
        rag_data = results[3].json() if not isinstance(results[3], Exception) else {}
        
        # Generate LLM response
        context = build_context(request.query, portfolio_data, market_data, earnings_data, rag_data)
        
        async with httpx.AsyncClient() as client:
            llm_response = await client.post(
                f"{LANG_AGENT_URL}/generate",
                json={"messages": [{"role": "user", "content": context}]}
            )
            llm_response.raise_for_status()
            ai_response = llm_response.json()["text"]
        
        return {
            "response": ai_response,
            "market_data": market_data,
            "portfolio_analysis": portfolio_data,
            "earnings_data": earnings_data,
            "relevant_documents": rag_data
        }
        
    except Exception as e:
        logger.error(f"Market brief generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def build_context(query: str, portfolio_data: Dict, market_data: Dict, earnings_data: Dict, rag_data: Dict) -> str:
    """Build comprehensive context for LLM"""
    
    context_parts = [
        f"User Query: {query}",
        "",
        "PORTFOLIO ANALYSIS:",
    ]
    
    # Add portfolio information
    if portfolio_data.get("analysis"):
        context_parts.append("Current portfolio holdings and risk exposure:")
        for holding in portfolio_data["analysis"][:5]:  # Top 5 holdings
            context_parts.append(
                f"- {holding['ticker']}: {holding['allocation_pct']:.1f}% allocation, "
                f"${holding['current_value']:,.2f} value"
            )
    
    context_parts.extend(["", "MARKET DATA:"])
    
    # Add market data
    if market_data.get("risk_exposure"):
        context_parts.append(f"Asia tech risk exposure: {market_data['risk_exposure']}%")
    
    # Add earnings data
    if earnings_data.get("surprise_pct"):
        context_parts.append(f"Recent earnings surprise: {earnings_data['surprise_pct']}%")
    
    context_parts.extend(["", "RECENT MARKET INTELLIGENCE:"])
    
    # Add RAG results
    if rag_data.get("results"):
        for doc in rag_data["results"][:3]:  # Top 3 relevant documents
            context_parts.append(f"- {doc.get('content', '')[:200]}...")
    
    context_parts.extend([
        "",
        "Please provide a concise, professional market brief addressing the user's query. ",
        "Focus on portfolio implications and actionable insights. ",
        "Keep the response under 150 words and speak as a knowledgeable portfolio advisor."
    ])
    
    return "\n".join(context_parts)

@app.post("/upsert-documents")
async def upsert_documents(documents: List[Dict]):
    """Proxy to retriever agent for document upsertion"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{RETRIEVER_AGENT_URL}/upsert", json=documents)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio")
async def get_portfolio():
    """Get current portfolio data"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RETRIEVER_AGENT_URL}/portfolio-analysis")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 