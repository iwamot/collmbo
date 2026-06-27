FROM dhi.io/python:3.14.6-debian13-dev@sha256:a0f83babf95ae5c0936254c6dfd55c621a6a46f5a23bb85c7db2973c385b51b6 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.25-debian13-dev@sha256:dee156d073d020d4d78e184f0f5a3f3f383c5c9db2d52e974c1bee4f0f6c94dd /uv /usr/local/bin/uv
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
