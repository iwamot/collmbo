FROM dhi.io/python:3.14.3-debian13-dev@sha256:2761ee5c85ff4f96b19c22b2885eaef76b6a1f8227622bd08adc734a25483cb4 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.10.11@sha256:3472e43b4e738cf911c99d41bb34331280efad54c73b1def654a6227bb59b2b4 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:9f0a28aace9221c9ecb02d8d3885ad7e8ac71ba71657b523f1a04b556daa3424 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
