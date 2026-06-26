FROM dhi.io/python:3.14.6-debian13-dev@sha256:278a2051e1ccb1f349d1d9f86da9a5a3cb8e52c122ee6a9da278993ecbc1090b AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.24-debian13-dev@sha256:c1e4b72ddc740e9ea27e7c86f5a4633c3e3454f7897e710092e9359a4314ae9f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:f0e074dca2de2f27be6e3536b13fb8cd9e44764b22daac237b9cbf2c9982be59 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
