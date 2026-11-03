FROM dhi.io/python:3.14.10-debian13-dev@sha256:e41db2192776cc39dbf3bbd210b4f9a6ee4f863c550ed85a25d39ec8002794a0 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.6-debian13-dev@sha256:88ac049cbfd9df80a07d1b4d1ccd926d18eac3e7c6d13a28221608820be8745f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:e0998e80e9d2cf6c956e5e1725c42549b55d697f815719bef301f7d7bdf1ecaf AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
