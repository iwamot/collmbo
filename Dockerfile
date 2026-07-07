FROM dhi.io/python:3.14.6-debian13-dev@sha256:6319d1cd1627611ed192368d2e05c467ca6e6e9b339682a4a5e7f0076b8d6190 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.26-debian13-dev@sha256:d316e04cd80e2c8fe8ee59b7f3c37330b9f4cd1d75185f31ee3851aa668b51a2 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:c27c6f9902521b7ab0ce8e453fef348e82dd4203da9816e8f3c582125baadc1c AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
