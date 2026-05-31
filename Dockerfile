FROM dhi.io/python:3.14.5-debian13-dev@sha256:3f8aaba36336fa6b7e97c2289903cfd115322f5b19286a4fdbed7083f0b1370d AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.17-debian13-dev@sha256:ff3a35307e979a23ac5567cda4ff214f59b3a225db93b34732a81f2a5186e586 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.5-debian13@sha256:ff889c0f24838055e6b1343a3c11abee14ec639d885efd257e7e636c0d1de6cc AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
