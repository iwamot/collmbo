FROM dhi.io/python:3.14.3-debian13-dev@sha256:2761ee5c85ff4f96b19c22b2885eaef76b6a1f8227622bd08adc734a25483cb4 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.10.10@sha256:cbe0a44ba994e327b8fe7ed72beef1aaa7d2c4c795fd406d1dbf328bacb2f1c5 /uv /usr/local/bin/uv
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
