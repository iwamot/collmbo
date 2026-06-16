FROM dhi.io/python:3.14.6-debian13-dev@sha256:3c5bdfca9edc21bbe3c3d1ff3b7dac2ef72fccaf146e7befcaf1c4c616edc010 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.21-debian13-dev@sha256:9492318cc94fa083999f6d5c61d46b39ea0a1319aa08c101a63d3fb4b5f873c2 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:e8b301a43adba8a2bdf31c284aa3993a2da62beebcc6d394af89fe1f3fa30c76 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
