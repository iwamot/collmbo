FROM dhi.io/python:3.14.7-debian13-dev@sha256:62168dc1438e8b555b195a2b31924d6a8db7ee6138493a4eb18e49763b537fde AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.7-debian13-dev@sha256:05f08301e2d9fcfd6615112c8cacc0870a3f303aae4116c9d34c70fa020613ec /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:3dc3500828bb01462358a408c2b2c71f492aff6597fd8ca600efefb1cd6dd644 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
