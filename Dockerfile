FROM dhi.io/python:3.14.7-debian13-dev@sha256:3fe8324735434c3471b243d23e16de4893d3ad67e8baa093a3a87c5d75ab1ccf AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.13-debian13-dev@sha256:557f852a17aaadf94f8fccaaf48e53519b7f0ddd1915baa62bf1cb173b116678 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:f59b1caff475a5fe8f54159b4e95013329d24ee583d6f869a68ded79b661b17d AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
