FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway injecte $PORT automatiquement comme variable d'environnement
# CMD utilise le shell (sh -c) pour que $PORT soit bien interprété
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
