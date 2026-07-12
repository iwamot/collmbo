FROM dhi.io/python:3.14.6-debian13-dev@sha256:db7b1fd1f71d338efca2edf1faf5dd71dccad749431920344060d28ab51c748e AS builder
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
