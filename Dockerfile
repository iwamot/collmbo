FROM dhi.io/python:3.14.7-debian13-dev@sha256:58fa6507f5442f3426b82f70cc89d7c547fd14a5a0ecdc429da8021133b49323 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.8-debian13-dev@sha256:cee85cafd2f7766b60c61cfa80f9c433c9b9697beb5f0345fead6d1e88374644 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:acd4a6acf99b3bfa3ff8c8d06f5232296f6e59bcac03e7ed4ba54ac8ffa41f0f AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
