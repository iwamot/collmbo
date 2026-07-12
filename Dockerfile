FROM dhi.io/python:3.14.6-debian13-dev@sha256:ef818f8ac2c2fb3c5b9e0b36ecb6fed60e07f43b2d7abcd895f961bb0be5094e AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.28-debian13-dev@sha256:b8106544c14b6bcce109363b20a8fe3fff6f64c455574cac7833f8d2a9823dcf /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:1b91e9693b8283a95c7e9cfce899396473091791174904529689e511fab7e602 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
