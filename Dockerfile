FROM dhi.io/python:3.14.6-debian13-dev@sha256:3891d709066bd6becbcce44677d9fdc02a7045b1b5eafe87d0ccd1e3b44820d9 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.30-debian13-dev@sha256:6fff0bb059d06fe2a4c929fec775e251c918af8725d26567dd9e09a5ea0050fd /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:c43e37b1d2c740bf924149f7ce015a79636a084a3fd755ac8c5ffc2f4a850b3e AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
