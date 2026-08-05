FROM dhi.io/python:3.14.6-debian13-dev@sha256:7d0fc232fe9bc11f60854c9bea7e40c3ecc4e185fa04ae93e8a23653e45f0b83 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.1-debian13-dev@sha256:79a8007d99385ed9ea7d657a516acf36428848e0dfdfa2f3886a45de84200f32 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:dba79d67b69005f82bb26954fc84bb9e1d050583ffdee2746eab63bce33f1a11 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
