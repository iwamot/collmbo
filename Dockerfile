FROM dhi.io/python:3.14.7-debian13-dev@sha256:a178ee6488b38c58c333eff50675717a314a15f006ede24ed121eaadc00c984b AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.5-debian13-dev@sha256:7dbb65f5b3386d3fe46e9f04821ce873ee089f4787da06c3026ae81ee977ad56 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:9525354fea02f28b9f51285b8e935807f2a2f98cfa684c5ea0ab1e7addaadf54 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
