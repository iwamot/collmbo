FROM dhi.io/python:3.14.8-debian13-dev@sha256:f342776dc2e3f2c3d9f37cf4cc182bbeb81b4eb4d3543357163aa5fa95bdc8bd AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.1-debian13-dev@sha256:8e8d4ecb8fded6c1cfb53e01462746c4d07be02fa33b079eae85805c914fc417 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:1f47877c0ddcce5f328550286a4b33b0f5e408455e396cd9056b3220a66aad40 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
