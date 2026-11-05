FROM dhi.io/python:3.14.10-debian13-dev@sha256:a19aadd1356349f6103a2b14dffcd7a4386bdcc5a2c63feaaa7ca50eef8bc2eb AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.7-debian13-dev@sha256:3370f1745687839e58461b54b2724212d4f72ecc80a7604f4b82db0a54774dbc /uv /usr/local/bin/uv
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
