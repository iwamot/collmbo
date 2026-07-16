FROM dhi.io/python:3.14.6-debian13-dev@sha256:9b72c38a520f44fafa1c4a3026e9b390eb3b4967c62d38be01400ecbb0232b65 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.29-debian13-dev@sha256:76b864a89528376063ceb27e24b09fbafc3c51efe1613122feb47081e815fb46 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:c82da5a1a30a6214f45c42def5b6f5b85981c7dc7a1802015a6ebf264675436d AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
