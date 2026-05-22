FROM dhi.io/python:3.14.5-debian13-dev@sha256:98f54e1d2ba526f945659f512f21e94c76bc750c0b7935cb75995e22939beb86 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.16-debian13-dev@sha256:6df4c9dd51b4aff4935ba6b552f8389b0cf1e074ab6fe03fe5c0193ce7e62b35 /uv /usr/local/bin/uv
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
