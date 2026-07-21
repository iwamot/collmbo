FROM dhi.io/python:3.14.6-debian13-dev@sha256:9b72c38a520f44fafa1c4a3026e9b390eb3b4967c62d38be01400ecbb0232b65 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.30-debian13-dev@sha256:6fff0bb059d06fe2a4c929fec775e251c918af8725d26567dd9e09a5ea0050fd /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:6b0b46d3451ae138084c8aea720b0cd458309540e656db66406065830305caef AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
