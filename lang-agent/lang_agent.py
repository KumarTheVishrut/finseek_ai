from fastapi import FastAPI, UploadFile, File, HTTPException
import tempfile
import os
import json
import subprocess
from typing import Dict, List
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lightweight Language Agent with Local LLM")

# Lightweight LLM setup - using HuggingFace Inference API for local-like experience
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
LLM_MODEL = "distilgpt2"  # Lightweight model
HF_API_URL = f"https://api-inference.huggingface.co/models/{LLM_MODEL}"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "lang-agent"}

@app.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    Mock speech-to-text - returns a sample transcript.
    In production, would integrate with cloud STT APIs.
    """
    try:
        # Mock response for demo - in production use cloud STT
        mock_transcripts = [
            "What's the current risk exposure in our Asia tech portfolio?",
            "How are earnings looking for TSMC this quarter?",
            "Give me a market brief on semiconductor stocks",
            "What's our portfolio allocation in Asian technology stocks?",
            "Any recent news affecting our Taiwan Semiconductor position?"
        ]
        
        # Use file size or name to pick a transcript for demo consistency
        file_size = len(await audio.read())
        selected_transcript = mock_transcripts[file_size % len(mock_transcripts)]
        
        logger.info(f"Mock STT transcript: {selected_transcript}")
        
        return {"transcript": selected_transcript}
        
    except Exception as e:
        logger.error(f"STT error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"STT failed: {str(e)}")

@app.post("/generate")
async def generate_text(payload: dict):
    """
    Generate text using lightweight local LLM via HuggingFace API.
    Falls back to template responses if API fails.
    """
    try:
        messages = payload.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Extract user content
        user_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_content = msg.get("content", "")
                break
        
        # Try to use HuggingFace API for lightweight LLM
        if HUGGINGFACE_API_KEY:
            try:
                response = await call_lightweight_llm(user_content)
                if response:
                    return {"text": response}
            except Exception as e:
                logger.warning(f"LLM API failed, falling back to templates: {e}")
        
        # Fallback to template responses
        response = generate_financial_response(user_content)
        return {"text": response}
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return {"text": "I apologize, but I'm experiencing technical difficulties. Please try again."}

async def call_lightweight_llm(prompt: str) -> str:
    """Call HuggingFace API for lightweight LLM generation"""
    try:
        # Prepare financial context prompt
        financial_prompt = f"""As a professional financial advisor specializing in Asia tech markets, please provide a concise analysis for: {prompt}

        Focus on portfolio implications and actionable insights. Keep response under 150 words.
        
        Analysis:"""
        
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": financial_prompt,
            "parameters": {
                "max_new_tokens": 150,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "").strip()
                
                # Clean up the response
                if generated_text:
                    # Remove any repetition of the prompt
                    if "Analysis:" in generated_text:
                        generated_text = generated_text.split("Analysis:")[-1].strip()
                    
                    # Ensure professional tone
                    if len(generated_text) > 20:
                        return generated_text
        
        return None
        
    except Exception as e:
        logger.warning(f"HuggingFace API call failed: {e}")
        return None

@app.post("/tts")
async def text_to_speech(payload: dict):
    """
    Lightweight TTS using system commands or mock.
    Returns audio file path for client consumption.
    """
    try:
        text = payload.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="No text provided for TTS")
        
        # Create mock audio file path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            audio_path = tmp_file.name
        
        # Try to use espeak if available, otherwise mock
        try:
            # Simple TTS using espeak (lightweight)
            subprocess.run([
                "espeak-ng", text, "-w", audio_path, "-s", "150"
            ], check=True, timeout=10)
            logger.info(f"Generated TTS audio: {audio_path}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # Fallback: create empty file for demo
            with open(audio_path, 'wb') as f:
                f.write(b'\x00' * 1024)  # Empty audio data
            logger.info(f"Mock TTS audio created: {audio_path}")
        
        return {"audio_file": audio_path}
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

def generate_financial_response(user_query: str) -> str:
    """
    Generate financial advice using business logic templates.
    Fallback when LLM is not available.
    """
    query_lower = user_query.lower()
    
    # Risk exposure templates
    if "risk" in query_lower and ("asia" in query_lower or "tech" in query_lower):
        return """Based on current analysis, your Asia tech portfolio shows moderate-to-high risk exposure at approximately 16.8%. 
Key factors include TSMC's semiconductor cycle position, Samsung's memory market dynamics, and regulatory environments in Taiwan and South Korea. 
Consider rebalancing if this exceeds your risk tolerance, especially given current geopolitical tensions affecting tech supply chains."""
    
    # Earnings templates
    elif "earnings" in query_lower and ("tsmc" in query_lower or "2330" in query_lower):
        return """TSMC recently reported Q4 earnings with an 8.5% positive surprise, beating expectations at $1.30 vs $1.20 expected EPS. 
Strong AI chip demand and 3nm process technology adoption are driving growth. However, monitor smartphone chip weakness and China export restrictions. 
The stock remains well-positioned for continued AI infrastructure buildout."""
    
    # Portfolio allocation templates
    elif "portfolio" in query_lower and "allocation" in query_lower:
        return """Your current Asia tech allocation stands at 34.2% of total portfolio value, concentrated in Taiwan Semiconductor (12.1%), Samsung (8.7%), and Alibaba (6.4%). 
This concentration presents both opportunity and risk. Consider diversifying across more Asia tech names or reducing allocation if it exceeds your strategic target."""
    
    # Market brief templates
    elif "market" in query_lower and ("brief" in query_lower or "semiconductor" in query_lower):
        return """Asia semiconductor markets are experiencing mixed signals. Taiwan and South Korea indices up 2.3% and 1.8% respectively on strong AI demand, 
but China tech faces headwinds from regulatory overhang. Memory chip pricing shows stabilization after 18-month downturn. 
Recommend maintaining quality positions while monitoring geopolitical developments."""
    
    # News and updates templates
    elif "news" in query_lower or "recent" in query_lower:
        return """Recent developments affecting Asian tech positions: TSMC guidance raised on AI chip demand, Samsung announces increased capex for advanced nodes, 
and China's stimulus measures supporting domestic tech consumption. Monitor upcoming earnings from key holdings and Fed policy impacts on growth tech valuations."""
    
    # General market commentary
    else:
        return """Current Asia tech markets show resilience despite macro headwinds. Key themes include AI infrastructure buildout, memory cycle recovery, and supply chain normalization. 
Maintain selective exposure to quality names with strong competitive moats. Consider profit-taking on overextended positions while accumulating on weakness in fundamentally sound companies."""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)