
FROM ghcr.io/astral-sh/uv:python3.12-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENV=.venv \
    UV_HTTP_TIMEOUT=300 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app


COPY pyproject.toml uv.lock ./


RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade --force-reinstall numpy thinc spacy



COPY core ./core
COPY models ./models
COPY assets ./assets

EXPOSE 8000
CMD [".venv/bin/pip", "freeze"]
