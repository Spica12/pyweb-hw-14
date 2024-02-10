# Образ Python
FROM python:3.10-slim

RUN pip install poetry
WORKDIR /app

COPY poetry.lock /app/poetry.lock
COPY pyproject.toml /app/pyproject.toml
RUN poetry install

COPY migrations/ /app/migrations
COPY src/ /app/src
COPY .env /app/.env
COPY alembic.ini /app/alembic.ini
COPY main.py /app/main.py


EXPOSE 8000
# CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
