FROM python:3.10-slim
WORKDIR /app

# Install system dependencies for audio processing and Whisper
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Whisper
RUN pip install openai-whisper

COPY lang_agent.py .

CMD ["uvicorn", "lang_agent:app", "--host", "0.0.0.0", "--port", "8003"]