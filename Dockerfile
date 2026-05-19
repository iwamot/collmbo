FROM dhi.io/python:3.14.5-debian13-dev@sha256:98f54e1d2ba526f945659f512f21e94c76bc750c0b7935cb75995e22939beb86 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.15-debian13-dev@sha256:58d227c6ea767e2c69173719a7d23fbb0a505f2337fea1217360d1f57c8115d3 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.5-debian13@sha256:4b669716481a34691219b9148cd81b27801111339a37fb0ebb2108149d4b99ca AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
