FROM dhi.io/python:3.14.4-debian13-dev@sha256:ef2fa2beab6aa256da894c5c4d7cd81483764f68fc7814f5e8bab26d2c89dc6c AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.11-debian13-dev@sha256:04ff4eaf35f55a9d7d7137aff6f7661839e224a8a1d6aa388e8ba4cef9386300 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.4-debian13@sha256:edb8192e94aef7bce840d1188f2e19b5fbd4f8aa7bd89bfb2c44eda0eca97346 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
