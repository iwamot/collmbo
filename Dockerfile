FROM dhi.io/python:3.14.10-debian13-dev@sha256:ea998331def4a8134f70ae63d2d57835ad8311c0af217208cb8ffc4ac354df67 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.7-debian13-dev@sha256:2585792a493eef2a76aa2910cdf62a99c3c8e9a60aabb95724357d9bfe3f3b90 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:1976c17f79525bf6c03e26256b24b5ab3f41e58b1189807b1a9af27592fd0088 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
