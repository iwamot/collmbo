FROM dhi.io/python:3.14.6-debian13-dev@sha256:a0f83babf95ae5c0936254c6dfd55c621a6a46f5a23bb85c7db2973c385b51b6 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.26-debian13-dev@sha256:ab50d8e53d83d267fedc3f48055dafcb1ae8eccc7eb64b7cc4e24c33e330bd1c /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:700be1a5996abb46d16a1fca6868c7f3bd7b87c4f7c09477d74312caea035305 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
