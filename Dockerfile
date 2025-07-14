FROM python:3.12 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN pip install poetry
RUN poetry config virtualenvs.in-project true
COPY pyproject.toml poetry.lock ./
RUN poetry install --only=main --no-root

FROM python:3.12-slim
WORKDIR /app

# Install debugging tools temporarily
RUN apt-get update && apt-get install -y \
    iputils-ping \
    dnsutils \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv .venv/
COPY src/ ./src/
COPY README.md ./

ENV PATH="/app/.venv/bin:$PATH"

# Environment variables for FastAPI
ARG WEB_HOST=0.0.0.0
ENV WEB_HOST=${WEB_HOST}

ARG WEB_PORT=8000
ENV WEB_PORT=${WEB_PORT}

EXPOSE ${WEB_PORT}

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
