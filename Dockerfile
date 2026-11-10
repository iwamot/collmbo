FROM dhi.io/python:3.14.10-debian13-dev@sha256:a38c43b0212baf7a5b6b0e2010a45e0c25e6cc37af044c1b8a6fdfd2c5b22ba1 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.7-debian13-dev@sha256:26db0233a71fc0f36b17be8a278ae59c13d1fdc5f94df7e51761c494fc76ef16 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:e21119acac57f9c336c0e7866ce8cfc61ef033e5db4c04d193e6df51088688d7 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
