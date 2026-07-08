FROM dhi.io/python:3.14.6-debian13-dev@sha256:1977c4a9624171ef582e641eb6f67adfc3f4b3ec0cb59345876f1928cda6f698 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.28-debian13-dev@sha256:16396cef2ff99fc9f39c134404a770135b3b80ca723e33ea87cde424e26bdbcf /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:975fb771f0685d6e0aa1212813c6f0c8c5062e77aa4d34daa5aabbb9b9713f1d AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
