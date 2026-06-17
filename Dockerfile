FROM dhi.io/python:3.14.6-debian13-dev@sha256:8eb7494ef9c51643958a11c386bd4fa3866d899c29c9cb4cf0e372a58ef7f023 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.21-debian13-dev@sha256:9492318cc94fa083999f6d5c61d46b39ea0a1319aa08c101a63d3fb4b5f873c2 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:4469b5c5732c2f2776df15ce8f5eb2a057e8ec092d3626ddbbebc10fc99d873d AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
