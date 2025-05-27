FROM python:3.9-slim
WORKDIR /app

# Install dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV ALPHA_VANTAGE_API_KEY=OO9T445FAP0I5LSV



ENV PORT=8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]