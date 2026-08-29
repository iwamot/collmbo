FROM dhi.io/python:3.14.7-debian13-dev@sha256:605fb5821aaa7d62c187110e66429b110379af0ba73e872afb5022504ba12178 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.7-debian13-dev@sha256:d6e842bdb79f2019425b0554117b598507bec8b7c44076c994d83c4b766d6a06 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:8be06a90a353d4f1bb9e44585ae183d6112e54dfbe8af6a06774c6f4285b221d AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
