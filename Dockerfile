FROM dhi.io/python:3.14.7-debian13-dev@sha256:8ca22a7569e6152307c766622994e0e0e0115c99f7c6583a73aa6f2cac022281 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.20-debian13-dev@sha256:8ff8eaf935f6a87aa2d2e3039ec827e0131ec9e973159a9a1e5663c570b546b2 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:e1a5bd571d9585d7eb80c8278b54b69a0e0bf5a9bb2b1424b9e4576374df6659 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
