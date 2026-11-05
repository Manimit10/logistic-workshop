FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 DB_PATH=/tmp/game.db
WORKDIR /srv
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app
COPY artifacts ./artifacts
RUN useradd -m appuser && chown -R appuser /srv
USER appuser
EXPOSE 8000
# Hosts such as Render and Cloud Run inject $PORT; default 8000 for local Docker.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
