FROM dhi.io/python:3.14.7-debian13-dev@sha256:5297e17c60a0d53e7ebca155a592cd6f740fc1c03a4bef98943878ff39da26a2 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.6-debian13-dev@sha256:02cc41e81791351292833cd8290160dfd4ecb6d5e580e577606718e094dafda0 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:aaf32d27c5a009dad4e279eb2d9aff2122519610d51e130c8d2729afc4458278 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
