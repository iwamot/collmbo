FROM dhi.io/python:3.14.4-debian13-dev@sha256:6d08fa284915b06d2fcc0405c0732871a6b95973174e43ceed16c4452a1233d5 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.8-debian13-dev@sha256:4de94fb0b05f911ca4cf039725ab7bb376567e69ebc3379f86a9a5a8a2fd7c8a /uv /usr/local/bin/uv
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
