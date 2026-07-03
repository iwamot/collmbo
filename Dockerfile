FROM dhi.io/python:3.14.6-debian13-dev@sha256:648e89d16f3bc513d2b235f5dcae593ea89b3954a7cb42da598a323e5148e06d AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.26-debian13-dev@sha256:ba767fb3c0c7477d321b039cab9ca8d8d22a25c618424721293aa72c6296135f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:bd6fd5ae321026e0f8dd49d64793227c339f6a821623a2de00968fddffcd4305 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
