# Use the official uv image matching your Python version
FROM ghcr.io/astral-sh/uv:python3.12-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./


COPY core/en_core_sci_sm-0.5.4.tar.gz /app/assets/
RUN uv sync --frozen --no-dev


RUN uv pip install --system /app/assets/en_core_sci_sm-0.5.4.tar.gz


COPY core ./core
COPY models ./models
COPY assets ./assets

EXPOSE 8000
CMD [".venv/bin/uvicorn", "core.backend:app", "--host", "0.0.0.0", "--port", "8000"]
