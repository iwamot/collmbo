FROM dhi.io/python:3.14.6-debian13-dev@sha256:51d88fce978c7f6ebc0bbd41d41850220b76ade7a8babdb13fd250bad6bc0930 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.3-debian13-dev@sha256:e73fa8c883220b83de607f6b8fbe787063d0057c7d7efd5db05d320d7ef499e1 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:4d38c7a342d804dcc8a212c08a76f8ad0a9da36b8b64bcab87da810d8a1ae5f4 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
