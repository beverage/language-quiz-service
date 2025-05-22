FROM python:latest

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/
COPY src /app/src

RUN poetry install --no-interaction --no-ansi

ARG WEB_HOST=0.0.0.0
ENV WEB_HOST=${WEB_HOST}

ARG WEB_PORT=8080
ENV WEB_PORT=${WEB_PORT}

EXPOSE ${WEB_PORT}

CMD ["poetry", "run", "lqconsole", "webserver", "start"]
