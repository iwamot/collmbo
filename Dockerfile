FROM dhi.io/python:3.14.3-debian13-dev@sha256:39179f907a549e007b7c5f40db421f0b68327d1683dfa9399985564183af64b9 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.10.10@sha256:cbe0a44ba994e327b8fe7ed72beef1aaa7d2c4c795fd406d1dbf328bacb2f1c5 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:16dae03aec93689d7f37de81286d56d77e9d836ac1944b690fbb4796c416e975 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
