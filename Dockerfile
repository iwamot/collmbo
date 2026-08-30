FROM dhi.io/python:3.14.7-debian13-dev@sha256:58fa6507f5442f3426b82f70cc89d7c547fd14a5a0ecdc429da8021133b49323 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.7-debian13-dev@sha256:05f08301e2d9fcfd6615112c8cacc0870a3f303aae4116c9d34c70fa020613ec /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:eeea2a4fbc5a741c557a9fea827d55753dda653672811ed9b9ffcf4f5a137697 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
