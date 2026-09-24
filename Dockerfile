FROM dhi.io/python:3.14.7-debian13-dev@sha256:42cd56dede69350b250398097287cbf1020d0ead0ad8cb4e179bd3bac1a98634 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.18-debian13-dev@sha256:f1100f071e8084c1df097a13dca90027675a18c6822beb4004165c09762e4383 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:7a5510681f1ece5a31b1f1540d3c9c3cc61b4503befe4394280b8602fcd0ff55 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
