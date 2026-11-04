FROM dhi.io/python:3.14.10-debian13-dev@sha256:625e9f54d27372396f320310465034c4353712a68cb7371ac7436f6b424ed560 AS builder
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
