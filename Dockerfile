FROM dhi.io/python:3.14.5-debian13-dev@sha256:6fb2fbaf1cbfedeac9b035bdc5538b237385164803254c8d47d784fc7395fe94 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.14-debian13-dev@sha256:41b494214b0c8edc9920e09b60bef9e0fe144fcc3324de7c7be153d955d8b373 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.5-debian13@sha256:06affe7f9b2dbca52f8ccdaeb2aef7d0e9096f52121d25a9a97d186fdbbd0827 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
