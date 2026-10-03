FROM dhi.io/python:3.14.8-debian13-dev@sha256:8592b76e5f4433ba868e2f6804789c27332dc8bb0ee3fe5c9e9fee304154461c AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.22-debian13-dev@sha256:051d45fa34a3c6ec2ff5424931199c0de74db075cd439dcb9eaa0a9d054bc8f0 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:1d19cb038f46dcc8cfe6fdff21fe70d32787e7cfea220cb131f340fa37cece08 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
