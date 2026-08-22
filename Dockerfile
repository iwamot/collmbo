FROM dhi.io/python:3.14.7-debian13-dev@sha256:f9c509bf2d000fc60c06e471ecd3fecbf57f7d9ded719e98a8e3a1eefa75db78 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.5-debian13-dev@sha256:23f8d7f67df585ab1ffa531631939d3c4174da5c465a3f3205992872b1008231 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:b7d1a17506b26aeb669d02517c62864fb7f7b165be45e48fde79bd42b9ff291e AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
