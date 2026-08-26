FROM dhi.io/python:3.14.7-debian13-dev@sha256:ef2d366cd461af05a717f2c245875d3cd24941d0727b0a34192ff097b5d6f807 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.5-debian13-dev@sha256:e64b448b1ec0e1c5936243230cd6c2dd6a80952d7275e54cb06263243a844cb5 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:4fe7c5d1dbeacefbf9c5e85146b63e9cf5511e8b361a77430a8511889fbd26e9 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
