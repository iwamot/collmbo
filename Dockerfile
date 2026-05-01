FROM dhi.io/python:3.14.4-debian13-dev@sha256:6d08fa284915b06d2fcc0405c0732871a6b95973174e43ceed16c4452a1233d5 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.8-debian13-dev@sha256:7836090fee6a7af9e14db5747eda9ad16b1886da3771f4677e9ee160e7722d54 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.4-debian13@sha256:e0d4c6347314a9d23f0f5efe9073bf5f7f51c4614622ae4240d29b1c2626a62c AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
