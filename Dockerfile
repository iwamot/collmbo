FROM dhi.io/python:3.14.8-debian13-dev@sha256:df0b3685c0d843d3d978c74b50f5fb7b55640d1fe24e90cb9ab4c5212307616d AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.24-debian13-dev@sha256:b9b1a2cb7e6fbcb4a3ed40296738082362e506d0ed222cbf524fefc7cdc7fd93 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:2af3a6573fdecaaeb5c5a8073ced2d511cafa38b4b1205ee8d4ab820b866bd20 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
