from fastapi import FastAPI, UploadFile, File, HTTPException
import subprocess
import json
import torch
import pyttsx3
from transformers import pipeline

app = FastAPI(title="Language Agent")

# Initialize TTS engine
tts_engine = pyttsx3.init()

# Configure device for model inference
device = 0 if torch.cuda.is_available() else -1

# Load DeepSeek model from Hugging Face Hub
generator = pipeline(
    "text-generation", 
    model="deepseek-ai/deepseek-vl2-small",
    trust_remote_code=True,
    device=device
)

@app.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    Transcribe audio to text using Whisper CLI.
    Expects uploaded audio file in WAV/MP3 format.
    """
    path = f"/tmp/{audio.filename}"
    with open(path, "wb") as f:
        f.write(await audio.read())
    try:
        res = subprocess.check_output([
            "whisper", path,
            "--model", "small",
            "--output_format", "json"
        ])
        data = json.loads(res)
        text = data.get("text", "")
        return {"transcript": text}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")

@app.post("/generate")
async def generate(payload: dict):
    """
    Generate text using DeepSeek model.
    Expects JSON: {"messages": [{"role": "user", "content": "..."}, ...]}
    Returns: {"text": "..."}
    """
    messages = payload.get("messages", [])
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    # Construct prompt
    prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    try:
        outputs = generator(
            prompt,
            max_length=512,
            num_return_sequences=1
        )
        full_text = outputs[0].get("generated_text", "")
        # Strip the prompt from the generated text
        response_text = full_text[len(prompt):].strip()
        return {"text": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

@app.post("/tts")
async def text_to_speech(payload: dict):
    """
    Convert text to speech using pyttsx3.
    Expects JSON: {"text": "Your response"}
    Returns: {"audio_file": "<path>"}
    """
    msg = payload.get("text", "")
    if not msg:
        raise HTTPException(status_code=400, detail="No text provided for TTS")
    out_path = "/tmp/output.wav"
    tts_engine.save_to_file(msg, out_path)
    tts_engine.runAndWait()
    return {"audio_file": out_path}