FROM dhi.io/python:3.14.6-debian13-dev@sha256:278a2051e1ccb1f349d1d9f86da9a5a3cb8e52c122ee6a9da278993ecbc1090b AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.24-debian13-dev@sha256:c1e4b72ddc740e9ea27e7c86f5a4633c3e3454f7897e710092e9359a4314ae9f /uv /usr/local/bin/uv
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
