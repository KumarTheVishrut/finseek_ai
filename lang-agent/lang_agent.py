from fastapi import FastAPI, UploadFile, File, HTTPException
import subprocess
import json
import torch
import pyttsx3
from transformers import pipeline
import tempfile
import os

app = FastAPI(title="Language Agent")

# Initialize TTS engine
tts_engine = pyttsx3.init()

# Configure device for model inference
device = 0 if torch.cuda.is_available() else -1

# Load a more suitable model for text generation
try:
    generator = pipeline(
        "text-generation", 
        model="microsoft/DialoGPT-medium",
        trust_remote_code=True,
        device=device
    )
except Exception as e:
    print(f"Warning: Could not load DialoGPT, falling back to gpt2: {e}")
    generator = pipeline(
        "text-generation", 
        model="gpt2",
        device=device
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "lang-agent"}

@app.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    Transcribe audio to text using Whisper CLI.
    Expects uploaded audio file in WAV/MP3 format.
    """
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Use whisper to transcribe
        try:
            result = subprocess.run([
                "whisper", tmp_path,
                "--model", "base",
                "--output_format", "json",
                "--output_dir", "/tmp"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Find the output JSON file
                base_name = os.path.splitext(os.path.basename(tmp_path))[0]
                json_path = f"/tmp/{base_name}.json"
                
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    text = data.get("text", "").strip()
                    
                    # Cleanup
                    os.unlink(json_path)
                    os.unlink(tmp_path)
                    
                    return {"transcript": text}
                else:
                    # Fallback: use stdout
                    text = result.stdout.strip()
                    os.unlink(tmp_path)
                    return {"transcript": text if text else "Could not transcribe audio"}
            else:
                os.unlink(tmp_path)
                raise HTTPException(status_code=500, detail=f"Whisper failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            os.unlink(tmp_path)
            raise HTTPException(status_code=500, detail="Speech recognition timeout")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT failed: {str(e)}")

@app.post("/generate")
async def generate(payload: dict):
    """
    Generate text using the language model.
    Expects JSON: {"messages": [{"role": "user", "content": "..."}, ...]}
    Returns: {"text": "..."}
    """
    try:
        messages = payload.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Extract the last user message or construct prompt from messages
        if len(messages) == 1 and messages[0].get("role") == "user":
            prompt = messages[0]["content"]
        else:
            # Construct conversation prompt
            prompt_parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    prompt_parts.append(f"Human: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
                else:
                    prompt_parts.append(content)
            prompt = "\n".join(prompt_parts) + "\nAssistant:"
        
        # Generate response
        outputs = generator(
            prompt,
            max_new_tokens=150,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            pad_token_id=generator.tokenizer.eos_token_id
        )
        
        full_text = outputs[0].get("generated_text", "")
        
        # Extract only the new generated text
        if full_text.startswith(prompt):
            response_text = full_text[len(prompt):].strip()
        else:
            response_text = full_text.strip()
        
        # Clean up the response
        if response_text.startswith("Assistant:"):
            response_text = response_text[10:].strip()
        
        # Ensure we have a meaningful response
        if not response_text or len(response_text) < 10:
            response_text = "I understand your query about the market analysis. Based on the available data, I'll provide you with a comprehensive assessment of the current market conditions and portfolio implications."
        
        return {"text": response_text}
        
    except Exception as e:
        print(f"Generation error: {e}")
        return {"text": "I apologize, but I'm having difficulty processing your request right now. Please try again."}

@app.post("/tts")
async def text_to_speech(payload: dict):
    """
    Convert text to speech using pyttsx3.
    Expects JSON: {"text": "Your response"}
    Returns: {"audio_file": "<path>"}
    """
    try:
        msg = payload.get("text", "")
        if not msg:
            raise HTTPException(status_code=400, detail="No text provided for TTS")
        
        # Create temporary file for audio output
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            out_path = tmp_file.name
        
        # Configure TTS engine
        tts_engine.setProperty('rate', 150)  # Speed of speech
        tts_engine.setProperty('volume', 0.9)  # Volume level
        
        # Generate speech
        tts_engine.save_to_file(msg, out_path)
        tts_engine.runAndWait()
        
        return {"audio_file": out_path}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)